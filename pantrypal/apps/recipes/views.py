"""Recipe views — AI-powered recipe suggestions and pantry deduction."""
import json
from datetime import datetime

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from pantrypal.apps.pantry.models import PantryItem
from pantrypal.services.openai_client import get_openai_client, has_openai_key


class GetRecipesView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if not has_openai_key():
            return Response(
                {'success': False, 'error': 'OpenAI API key not configured', 'status': 'CONFIG_ERROR'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        pantry_items = request.data.get('pantryItems')
        if not pantry_items:
            return Response(
                {'success': False, 'error': 'Pantry items are required', 'status': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        def parse_date(date_str):
            try:
                return datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
            except (ValueError, TypeError):
                try:
                    return datetime.strptime(date_str, '%Y-%m-%d')
                except (ValueError, TypeError):
                    return datetime.max

        pantry_items.sort(key=lambda x: parse_date(x.get('expirationDate', '')))

        pantry_list = '\n'.join([
            f"- {item.get('quantity', 'some')} {item.get('quantityType', '')} "
            f"{item.get('productName', 'Unknown')} "
            f"(Category: {item.get('productCategory', 'Unknown')}, "
            f"Expires: {item.get('expirationDate', 'unknown')})"
            for item in pantry_items
        ])

        prompt = f"""Based on these ingredients in my pantry, suggest 6 different recipes I could make.
The first three recipes should prioritize recipes that use ingredients with the earliest expiration dates, while maintaining recipe quality. The other three don't need to prioritize expiration date.

Here are my pantry items, sorted by expiration date (earliest first):
{pantry_list}

For each recipe, provide the following information in EXACTLY this format:

1. Recipe name: [Name of the recipe]
2. Brief description: [A short description of the recipe]
3. Ingredients: [List of ingredients with amounts]
4. Instructions: [Step-by-step instructions]
5. Cooking time: [Approximate cooking time]
6. Urgency: [Either "Urgent" or "Not Urgent"]

Now, suggest 6 recipes following the exact format above.
"""

        client = get_openai_client()
        try:
            recipe_response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[
                    {'role': 'system', 'content': 'You are a helpful cooking assistant that creates recipes based on available ingredients.'},
                    {'role': 'user', 'content': prompt},
                ],
                temperature=0.7,
                max_tokens=1500,
            )
            recipe_text = recipe_response.choices[0].message.content.strip()

            parser_prompt = f"""Parse the following recipe text into a structured JSON format with an array of recipe objects.
Each recipe object should have fields for: name, description, ingredients (as an array), instructions (as an array of steps), cookingTime, and mealType.

Recipe text:
{recipe_text}

Respond with ONLY valid JSON, no explanation or additional text.
"""
            parser_response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[
                    {'role': 'system', 'content': 'You are a precise JSON parser that converts recipe text to structured data.'},
                    {'role': 'user', 'content': parser_prompt},
                ],
                temperature=0,
                max_tokens=1500,
            )
            parsed_recipes = parser_response.choices[0].message.content.strip()

            return Response({'success': True, 'recipes': parsed_recipes, 'pantryItems': pantry_items})

        except Exception as e:
            return Response(
                {'success': False, 'error': 'Server error', 'status': 'SERVER_ERROR', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CookRecipeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not has_openai_key():
            return Response(
                {'success': False, 'error': 'OpenAI API key not configured', 'status': 'CONFIG_ERROR'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        recipe = request.data.get('recipe')
        pantry_items = request.data.get('pantryItems')
        if not recipe or not pantry_items:
            return Response(
                {'success': False, 'error': 'Recipe and pantry items are required', 'status': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        prompt = f"""
You are a helpful cooking assistant. You need to determine which pantry items should be used for a recipe and how much of each item should be used.

Recipe:
Name: {recipe.get('name', 'Unknown Recipe')}
Ingredients: {', '.join(recipe.get('ingredients', []))}

Available Pantry Items (with their IDs):
{json.dumps(pantry_items, indent=2)}

For each ingredient in the recipe, identify the matching pantry item(s) and specify:
1. The pantryID of the item to use
2. The quantity to deduct from the pantry
3. If the item should be completely removed (quantity becomes 0)

Return your response as a JSON array of objects:
[
  {{
    "pantryID": 123,
    "quantityToDeduct": 2,
    "removeCompletely": false
  }}
]

Only include pantry items that should be modified.
"""

        client = get_openai_client()
        try:
            ai_response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[
                    {'role': 'system', 'content': 'You are a precise cooking assistant that helps track pantry inventory.'},
                    {'role': 'user', 'content': prompt},
                ],
                temperature=0,
                max_tokens=1000,
            )
            content = ai_response.choices[0].message.content.strip()
            # Strip markdown fences if present
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
            items_to_update = json.loads(content.strip())

        except json.JSONDecodeError as e:
            return Response(
                {'success': False, 'error': 'Failed to parse AI response', 'status': 'SERVER_ERROR', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        updated_items = []
        removed_items = []

        for item_data in items_to_update:
            pantry_id = item_data.get('pantryID')
            quantity_to_deduct = item_data.get('quantityToDeduct', 0)
            remove_completely = item_data.get('removeCompletely', False)

            try:
                pantry_item = PantryItem.objects.get(pantry_id=pantry_id, user=request.user)
            except PantryItem.DoesNotExist:
                continue

            if remove_completely:
                pantry_item.delete()
                removed_items.append(pantry_id)
            else:
                new_qty = max(0, float(pantry_item.quantity) - quantity_to_deduct)
                if new_qty <= 0:
                    pantry_item.delete()
                    removed_items.append(pantry_id)
                else:
                    pantry_item.quantity = new_qty
                    pantry_item.save()
                    updated_items.append(pantry_id)

        return Response({
            'success': True,
            'message': 'Recipe cooked successfully',
            'updatedItems': updated_items,
            'removedItems': removed_items,
        })
