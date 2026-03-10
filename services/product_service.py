from psycopg2.extras import RealDictCursor

from .ai_service import get_gpt_category
from .db import get_db_connection


def find_product_in_db(upc: str):
    """Check if a product exists in the database."""
    try:
        conn = get_db_connection()
        if not conn:
            return None, "Database connection failed"

        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM products WHERE productUPC = %s", (upc,))
        product = cur.fetchone()
        cur.close()
        conn.close()
        return product, None
    except Exception as e:
        return None, str(e)


def save_product_to_db(product_data: dict):
    """Save or update product information in the database."""
    try:
        conn = get_db_connection()
        if not conn:
            return False, "Database connection failed"

        raw_category = product_data.get('category', '')
        mapped_category = get_gpt_category(product_data)

        upc = product_data.get('upc', '')
        title = product_data.get('title', '')
        description = product_data.get('description', '')[:515] if product_data.get('description') else ''
        brand = product_data.get('brand', '')
        lowest_price = float(product_data.get('lowest_recorded_price', 0.0))
        highest_price = float(product_data.get('highest_recorded_price', 0.0))
        currency = product_data.get('currency', 'USD')
        images = product_data.get('images', [])
        model = product_data.get('model', '')
        color = product_data.get('color', '')
        size = product_data.get('size', '')
        dimension = product_data.get('dimension', '')
        weight = product_data.get('weight', '')

        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO products (
                productUPC, productName, productDescription, productBrand,
                productCategory, productLowestPrice, productHighestPrice,
                productCurrency, productImages, productModel, productColor,
                productSize, productDimension, productWeight
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (productUPC) DO UPDATE SET
                productName = EXCLUDED.productName,
                productDescription = EXCLUDED.productDescription,
                productBrand = EXCLUDED.productBrand,
                productCategory = EXCLUDED.productCategory,
                productLowestPrice = EXCLUDED.productLowestPrice,
                productHighestPrice = EXCLUDED.productHighestPrice,
                productCurrency = EXCLUDED.productCurrency,
                productImages = EXCLUDED.productImages,
                productModel = EXCLUDED.productModel,
                productColor = EXCLUDED.productColor,
                productSize = EXCLUDED.productSize,
                productDimension = EXCLUDED.productDimension,
                productWeight = EXCLUDED.productWeight
        """,
            (
                upc,
                title,
                description,
                brand,
                mapped_category,
                lowest_price,
                highest_price,
                currency,
                images,
                model,
                color,
                size,
                dimension,
                weight,
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        print(f"Failed to cache product: {str(e)}")
        print(f"Full product data that caused error: {product_data}")
        return False, str(e)
