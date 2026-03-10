import json

from flask import Blueprint, request, jsonify

from auth import token_required
from services.openai_client import has_openai_key, openai_client

recipe_bp = Blueprint('recipes', __name__, url_prefix='/api')


@recipe_bp.route('/get-recipes', methods=['POST'])
def get_recipes():
    if not has_openai_key():
        return jsonify({'success': False, 'error': 'OpenAI API key not configured', 'status': 'CONFIG_ERROR'}), 503

    try:
        request_data = request.get_json()
        if not request_data or 'pantryItems' not in request_data:
            return jsonify({'success': False, 'error': 'Pantry items are required in the request body', 'status': 'VALIDATION_ERROR'}), 400

        pantry_items = request_data['pantryItems']
        if not pantry_items:
            return jsonify({'success': False, 'error': 'No pantry items provided', 'status': 'NOT_FOUND'}), 404

        def parse_date(date_str):
            from datetime import datetime

            try:
                return datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
            except ValueError:
                return datetime.strptime(date_str, '%Y-%m-%d')

        pantry_items.sort(key=lambda x: parse_date(x.get('expirationDate', '9999-12-31')))

        pantry_list = "\n".join(
            [
                f"- {item.get('quantity', 'some')} {item.get('quantityType', '')} {item.get('productName', 'Unknown')} (Category: {item.get('productCategory', 'Unknown')}, Expires: {item.get('expirationDate', 'unknown')})"
                for item in pantry_items
            ]
        )

        prompt = f"""Based on these ingredients in my pantry, suggest 6 different recipes I could make. 
The first three recipes should prioritize recipes that use ingredients with the earliest expiration dates, while maintaining recipe quality. The other three, don't need to prioritize expiration date.

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

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful cooking assistant that creates recipes based on available ingredients."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1500,
        )

        recipe_text = response.choices[0].message.content.strip()

        parser_prompt = f"""Parse the following recipe text into a structured JSON format with an array of recipe objects.
Each recipe object should have fields for: name, description, ingredients (as an array), instructions (as an array of steps), cookingTime, and mealType.

Recipe text:
{recipe_text}

Respond with ONLY valid JSON, no explanation or additional text.
"""

        parser_response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a precise JSON parser that converts recipe text to structured data."},
                {"role": "user", "content": parser_prompt},
            ],
            temperature=0,
            max_tokens=1500,
        )

        parsed_recipes = parser_response.choices[0].message.content.strip()

        return jsonify({'success': True, 'recipes': parsed_recipes, 'pantryItems': pantry_items})

    except Exception as e:
        return jsonify({'success': False, 'error': 'Server error', 'status': 'SERVER_ERROR', 'details': str(e)}), 500


@recipe_bp.route('/cook-recipe', methods=['POST'])
@token_required
def cook_recipe(current_user_id):
    if not has_openai_key():
        return jsonify({'success': False, 'error': 'OpenAI API key not configured', 'status': 'CONFIG_ERROR'}), 503

    try:
        data = request.get_json()
        if not data or 'recipe' not in data or 'pantryItems' not in data:
            return jsonify({'success': False, 'error': 'Recipe and pantry items are required', 'status': 'VALIDATION_ERROR'}), 400

        recipe = data['recipe']
        pantry_items = data['pantryItems']

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

Return your response as a JSON array of objects with the following structure:
[
  {{
    "pantryID": 123,
    "quantityToDeduct": 2,
    "removeCompletely": false
  }},
  ...
]

Only include pantry items that should be modified. Be precise with quantities and ensure they match the recipe requirements.
"""

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a precise cooking assistant that helps track pantry inventory."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=1000,
        )

        content = response.choices[0].message.content.strip()
        if content.startswith("```json") or content.startswith("```"):
            content = content.replace("```json", "", 1).replace("```", "", 1).strip()
            if content.endswith("```"):
                content = content[:-3].strip()

        items_to_update = json.loads(content)

        conn = None
        try:
            from services.db import get_db_connection

            conn = get_db_connection()
            if not conn:
                return jsonify({'success': False, 'error': 'Database connection failed', 'status': 'DB_ERROR'}), 503

            cur = conn.cursor()
            updated_items = []
            removed_items = []

            for item in items_to_update:
                pantry_id = item.get('pantryID')
                quantity_to_deduct = item.get('quantityToDeduct', 0)
                remove_completely = item.get('removeCompletely', False)

                cur.execute(
                    "SELECT * FROM usersProducts WHERE pantryID = %s AND userID = %s",
                    (pantry_id, current_user_id),
                )
                pantry_item = cur.fetchone()
                if not pantry_item:
                    continue

                if remove_completely:
                    cur.execute("DELETE FROM usersProducts WHERE pantryID = %s", (pantry_id,))
                    removed_items.append(pantry_id)
                else:
                    new_quantity = max(0, float(pantry_item['quantity']) - quantity_to_deduct)
                    if new_quantity <= 0:
                        cur.execute("DELETE FROM usersProducts WHERE pantryID = %s", (pantry_id,))
                        removed_items.append(pantry_id)
                    else:
                        cur.execute(
                            "UPDATE usersProducts SET quantity = %s WHERE pantryID = %s RETURNING *",
                            (new_quantity, pantry_id),
                        )
                        updated_item = cur.fetchone()
                        updated_items.append(updated_item)

            conn.commit()
            cur.close()
            conn.close()

            return jsonify({'success': True, 'message': 'Recipe cooked successfully', 'updatedItems': updated_items, 'removedItems': removed_items})
        except Exception as db_error:
            if conn:
                conn.rollback()
                conn.close()
            return jsonify({'success': False, 'error': 'Database error', 'status': 'DB_ERROR', 'details': str(db_error)}), 503

    except json.JSONDecodeError as json_error:
        return jsonify({'success': False, 'error': 'Failed to parse AI response', 'status': 'SERVER_ERROR', 'details': str(json_error)}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': 'Server error', 'status': 'SERVER_ERROR', 'details': str(e)}), 500
