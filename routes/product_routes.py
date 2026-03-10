from datetime import datetime

from flask import Blueprint, request, jsonify

from auth import token_required
from services.ai_service import get_days_to_expire, get_gpt_category, estimate_expiry_date
from services.db import get_db_connection
from services.product_service import find_product_in_db, save_product_to_db
from services.upc_service import call_upc_api, validate_upc

product_bp = Blueprint('products', __name__, url_prefix='/api')


@product_bp.route('/lookup-upc', methods=['GET'])
def lookup_upc():
    try:
        upc = request.args.get('upc')
        if not upc:
            return jsonify({
                "success": False,
                "source": None,
                "cached": False,
                "items": None,
                "error": "UPC is required",
                "status": "VALIDATION_ERROR",
                "details": None,
            }), 400

        is_valid, result = validate_upc(upc)
        if not is_valid:
            return jsonify({
                "success": False,
                "source": None,
                "cached": False,
                "items": None,
                "error": "Invalid UPC format",
                "status": "VALIDATION_ERROR",
                "details": result,
            }), 400

        upc = result

        product, db_error = find_product_in_db(upc)
        if db_error:
            return jsonify({
                "success": False,
                "source": None,
                "cached": False,
                "items": None,
                "error": "Database error",
                "status": "DB_ERROR",
                "details": db_error,
            }), 503

        if product:
            normalized_product = {
                "title": product["productname"],
                "brand": product["productbrand"],
                "category": product["productcategory"],
                "description": product["productdescription"],
                "lowest_recorded_price": product["productlowestprice"],
                "highest_recorded_price": product["producthighestprice"],
                "currency": product["productcurrency"],
                "images": product["productimages"],
                "model": product["productmodel"],
                "color": product["productcolor"],
                "size": product["productsize"],
                "dimension": product["productdimension"],
                "weight": product["productweight"],
                "upc": product["productupc"],
            }

            gpt_category = get_gpt_category(normalized_product)
            days_to_expire = get_days_to_expire(normalized_product)
            expiry_date = estimate_expiry_date(days_to_expire)
            current_date = datetime.now().strftime("%Y-%m-%d")

            normalized_product["category"] = gpt_category
            normalized_product["expiryDate"] = expiry_date
            normalized_product["purchaseDate"] = current_date

            return jsonify({
                "success": True,
                "source": "database",
                "cached": True,
                "items": [normalized_product],
                "error": None,
                "status": None,
                "details": None,
            })

        response = call_upc_api(upc)
        if not response:
            return jsonify({
                "success": False,
                "source": "api",
                "cached": False,
                "items": None,
                "error": "API request failed",
                "status": "API_ERROR",
                "details": "Failed to connect to UPC API",
            }), 503

        if response.status_code != 200:
            return jsonify({
                "success": False,
                "source": "api",
                "cached": False,
                "items": None,
                "error": "UPC lookup failed",
                "status": "API_ERROR",
                "details": f"API returned status code: {response.status_code}",
            }), response.status_code

        api_data = response.json()

        if api_data.get('product'):
            gpt_category = get_gpt_category(api_data['product'])
            current_date = datetime.now().strftime("%Y-%m-%d")
            days_to_expire = get_days_to_expire(api_data['product'])
            expiry_date = estimate_expiry_date(days_to_expire)

            product_data = {
                'upc': api_data.get('code'),
                'title': api_data['product'].get('name'),
                'brand': api_data['product'].get('brand'),
                'category': gpt_category,
                'description': api_data['product'].get('description'),
                'images': [api_data['product'].get('imageUrl')] if api_data['product'].get('imageUrl') else [],
                'model': '',
                'color': next((spec[1] for spec in api_data['product'].get('specs', []) if spec[0] == 'Color'), ''),
                'size': next((spec[1] for spec in api_data['product'].get('specs', []) if spec[0] == 'Size'), ''),
                'dimension': next((f"{spec[1]}" for spec in api_data['product'].get('specs', []) if any(dim in spec[0].lower() for dim in ['height', 'width', 'length'])), ''),
                'weight': next((spec[1] for spec in api_data['product'].get('specs', []) if 'weight' in spec[0].lower()), ''),
                'lowest_recorded_price': 0.0,
                'highest_recorded_price': 0.0,
                'currency': 'USD',
                'purchaseDate': current_date,
                'expiryDate': expiry_date,
            }

            success, save_error = save_product_to_db(product_data)
            if not success:
                return jsonify({
                    "success": True,
                    "source": "api",
                    "cached": False,
                    "items": [product_data],
                    "error": None,
                    "status": None,
                    "details": f"Failed to cache: {save_error}",
                })

            return jsonify({
                "success": True,
                "source": "api",
                "cached": True,
                "items": [product_data],
                "error": None,
                "status": None,
                "details": None,
            })

        return jsonify({
            "success": False,
            "source": "api",
            "cached": False,
            "items": None,
            "error": "Product not found",
            "status": "NOT_FOUND",
            "details": None,
        }), 404

    except Exception as e:
        print(f"Server error in lookup_upc: {str(e)}")
        return jsonify({
            "success": False,
            "source": None,
            "cached": False,
            "items": None,
            "error": "Server error",
            "status": "SERVER_ERROR",
            "details": str(e),
        }), 500


@product_bp.route('/products', methods=['POST'])
@token_required
def add_product(current_user_id):
    try:
        data = request.get_json()
        if 'productUPC' not in data or not data['productUPC']:
            return jsonify({'success': False, 'error': 'Product UPC is required', 'status': 'VALIDATION_ERROR'}), 400
        if 'productName' not in data or not data['productName']:
            return jsonify({'success': False, 'error': 'Product name is required', 'status': 'VALIDATION_ERROR'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed', 'status': 'DB_ERROR'}), 503

        cur = conn.cursor()
        cur.execute("SELECT * FROM products WHERE productUPC = %s", (data['productUPC'],))
        existing_product = cur.fetchone()

        if existing_product:
            update_fields = []
            update_values = []
            for key, value in data.items():
                if key != 'productUPC':
                    update_fields.append(f"{key} = %s")
                    update_values.append(value)
            update_values.append(data['productUPC'])
            update_query = f"""
                UPDATE products 
                SET {', '.join(update_fields)}
                WHERE productUPC = %s
                RETURNING *
            """
            cur.execute(update_query, update_values)
        else:
            fields = []
            placeholders = []
            values = []
            for key, value in data.items():
                fields.append(key)
                placeholders.append("%s")
                values.append(value)
            insert_query = f"""
                INSERT INTO products ({', '.join(fields)})
                VALUES ({', '.join(placeholders)})
                RETURNING *
            """
            cur.execute(insert_query, values)

        product = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'success': True, 'product': product})
    except Exception as e:
        return jsonify({'success': False, 'error': 'Server error', 'status': 'SERVER_ERROR', 'details': str(e)}), 500


@product_bp.route('/products/<int:product_upc>', methods=['GET'])
@token_required
def get_product_by_upc(current_user_id, product_upc):
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed', 'status': 'DB_ERROR'}), 503

        cur = conn.cursor()
        cur.execute(
            """
            SELECT 
                productUPC, 
                productName, 
                productDescription, 
                productBrand, 
                productModel, 
                productColor, 
                productSize, 
                productDimension, 
                productWeight, 
                productCategory, 
                productLowestPrice, 
                productHighestPrice, 
                productCurrency, 
                productImages
            FROM products 
            WHERE productUPC = %s
        """,
            (product_upc,),
        )
        product = cur.fetchone()

        if not product:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Product not found', 'status': 'NOT_FOUND'}), 404

        product_data = {
            'productUPC': product[0],
            'productName': product[1],
            'productDescription': product[2],
            'productBrand': product[3],
            'productModel': product[4],
            'productColor': product[5],
            'productSize': product[6],
            'productDimension': product[7],
            'productWeight': product[8],
            'productCategory': product[9],
            'productLowestPrice': float(product[10]) if product[10] is not None else None,
            'productHighestPrice': float(product[11]) if product[11] is not None else None,
            'productCurrency': product[12],
            'productImages': product[13] if product[13] else [],
        }

        cur.close()
        conn.close()

        return jsonify({'success': True, 'product': product_data})
    except Exception as e:
        print(f"Error getting product by UPC: {str(e)}")
        return jsonify({'success': False, 'error': 'Server error', 'status': 'SERVER_ERROR', 'details': str(e)}), 500
