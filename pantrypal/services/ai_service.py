"""AI service — GPT-based categorization and expiry estimation."""
from datetime import datetime, timedelta

from .openai_client import get_openai_client, has_openai_key

FOOD_CATEGORIES = [
    'Fruits & Vegetables', 'Meat & Seafood', 'Dairy & Eggs', 'Bread & Bakery',
    'Pantry Staples', 'Snacks', 'Beverages', 'Frozen Foods', 'Canned Goods',
    'Condiments & Sauces', 'Baking Supplies', 'Breakfast Foods', 'Pasta & Rice',
    'Herbs & Spices', 'Ready-to-Eat Meals', 'Baby Food & Formula', 'Pet Food', 'Other',
]


def _build_category_prompt(product_data: dict) -> str:
    product_info = f"""
Product Name: {product_data.get('title', product_data.get('name', ''))}
Brand: {product_data.get('brand', '')}
Description: {product_data.get('description', '')}
"""
    return (
        f"Based on the following product information, categorize this food item into EXACTLY ONE of these categories: "
        f"{', '.join(FOOD_CATEGORIES)}.\n"
        f"Respond with ONLY the category name, nothing else.\n\n"
        f"Product Information:\n{product_info}\n\n"
        f"Remember:\n"
        f"1. Respond with EXACTLY ONE category from the list\n"
        f"2. Do not add any explanation or additional text\n"
        f"3. If unsure, use the most specific category that fits, or 'Other' as last resort"
    )


def get_gpt_category(product_data: dict) -> str:
    """Use OpenAI to map a product to a known category."""
    if not has_openai_key():
        return 'Other'

    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a precise food categorization assistant. You only respond with exact category names from the provided list.',
                },
                {'role': 'user', 'content': _build_category_prompt(product_data)},
            ],
            temperature=0,
            max_tokens=20,
        )
        category = response.choices[0].message.content.strip()
        return category if category in FOOD_CATEGORIES else 'Other'
    except Exception as e:
        print(f'GPT categorization error: {e}')
        return 'Other'


def get_days_to_expire(product_data: dict) -> str:
    """Use OpenAI to estimate days until expiry for a product."""
    if not has_openai_key():
        return 'n/a'

    prompt = (
        f"You are a food expiration expert. Your task is to analyze product information and output ONLY a number "
        f"representing days until expiry, or \"n/a\" for non-perishable items.\n"
        f"Rules:\n"
        f"1. Output ONLY a number (no text, units, or explanation) representing days until expiry\n"
        f"2. Output ONLY \"n/a\" for non-perishable items\n"
        f"3. If uncertain, use conservative estimates based on product category\n"
        f"4. General guidelines: Fresh produce 3-14 days, Dairy 7-21 days, Fresh meat 3-7 days, "
        f"Bread 5-7 days, Ready meals 3-5 days, Frozen foods 180 days\n\n"
        f"Product to analyze:\n{product_data}\n\n"
        f"Remember: Output ONLY a number or \"n/a\". No other text."
    )

    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {
                    'role': 'system',
                    'content': "You are a precise food expiration expert. You only respond with numbers or 'n/a'.",
                },
                {'role': 'user', 'content': prompt},
            ],
            temperature=1,
            max_tokens=10,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f'Error getting days to expire: {e}')
        return 'n/a'


def estimate_expiry_date(days_to_expire: str) -> str:
    """Return an ISO date string for expiration based on days_to_expire."""
    today = datetime.now()
    if days_to_expire == 'n/a':
        return (today + timedelta(days=730)).strftime('%Y-%m-%d')
    try:
        return (today + timedelta(days=int(days_to_expire))).strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        return today.strftime('%Y-%m-%d')
