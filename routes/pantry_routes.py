from flask import Blueprint, request, jsonify

from psycopg2.extras import RealDictCursor
from auth import token_required
from services.db import get_db_connection

pantry_bp = Blueprint('pantry', __name__, url_prefix='/api')

@pantry_bp.route('/pantry', methods=['POST'])
@token_required
def add_to_pantry(current_user_id):
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['productUPC', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'{field} is required',
                    'status': 'VALIDATION_ERROR'
                }), 400
        
        # Convert productUPC to string to handle large numbers properly
        product_upc = str(data['productUPC'])
        quantity = data['quantity']
        quantity_type = data.get('quantityType', 'items')  # Default to 'items' if not provided
        date_purchased = data.get('date_purchased')
        expiration_date = data.get('expiration_date')
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database connection failed',
                'status': 'DB_ERROR'
            }), 503
        
        cur = conn.cursor()
        
        # First, check if the product exists
        cur.execute("SELECT productUPC FROM products WHERE productUPC = %s", (product_upc,))
        product = cur.fetchone()
        
        if not product:
            cur.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Product not found',
                'status': 'NOT_FOUND'
            }), 404
        
        # Insert into usersProducts (not pantry)
        cur.execute("""
            INSERT INTO usersProducts 
            (userID, productUPC, quantity, quantityType, date_purchased, expiration_date) 
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING pantryID
        """, (current_user_id, product_upc, quantity, quantity_type, date_purchased, expiration_date))
        
        # Get the newly created pantry item ID
        new_pantry_id = cur.fetchone()[0]
        conn.commit()
        
        # Get the complete pantry item details
        cur.execute("""
            SELECT 
                up.pantryID, 
                up.userID, 
                up.productUPC, 
                up.quantity, 
                up.quantityType, 
                up.date_purchased, 
                up.expiration_date,
                p.productName,
                p.productBrand
            FROM usersProducts up
            JOIN products p ON up.productUPC = p.productUPC
            WHERE up.pantryID = %s
        """, (new_pantry_id,))
        
        pantry_item = cur.fetchone()
        cur.close()
        conn.close()
        
        if not pantry_item:
            return jsonify({
                'success': False,
                'error': 'Failed to retrieve added pantry item',
                'status': 'SERVER_ERROR'
            }), 500
        
        # Format the response
        pantry_data = {
            'pantryID': pantry_item[0],
            'userID': pantry_item[1],
            'productUPC': pantry_item[2],
            'quantity': pantry_item[3],
            'quantityType': pantry_item[4],
            'date_purchased': pantry_item[5].isoformat() if pantry_item[5] else None,
            'expiration_date': pantry_item[6].isoformat() if pantry_item[6] else None,
            'productName': pantry_item[7],
            'productBrand': pantry_item[8]
        }
        
        return jsonify({
            'success': True,
            'message': 'Product added to pantry successfully',
            'pantryItem': pantry_data
        })
        
    except Exception as e:
        print(f"Error adding to pantry: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Server error',
            'status': 'SERVER_ERROR',
            'details': str(e)
        }), 500

@pantry_bp.route('/pantry/<int:pantry_id>', methods=['PUT'])
@token_required
def update_pantry_item(current_user_id, pantry_id):
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No update data provided',
                'status': 'VALIDATION_ERROR'
            }), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database connection failed',
                'status': 'DB_ERROR'
            }), 503
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verify pantry item exists and belongs to user
        cur.execute(
            "SELECT * FROM usersProducts WHERE pantryID = %s AND userID = %s",
            (pantry_id, current_user_id)
        )
        pantry_item = cur.fetchone()
        
        if not pantry_item:
            cur.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Pantry item not found or does not belong to user',
                'status': 'NOT_FOUND'
            }), 404
        
        # Build update query
        update_fields = []
        update_values = []
        
        for key, value in data.items():
            if key in ['quantity', 'quantityType', 'expiration_date', 'date_purchased']:
                update_fields.append(f"{key} = %s")
                update_values.append(value)
        
        if not update_fields:
            cur.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'No valid fields to update',
                'status': 'VALIDATION_ERROR'
            }), 400
        
        # Add pantry_id for WHERE clause
        update_values.append(pantry_id)
        
        update_query = f"""
            UPDATE usersProducts 
            SET {', '.join(update_fields)}
            WHERE pantryID = %s
            RETURNING *
        """
        
        cur.execute(update_query, update_values)
        updated_item = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'pantry_item': updated_item
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Server error',
            'status': 'SERVER_ERROR',
            'details': str(e)
        }), 500

@pantry_bp.route('/pantry/<int:pantry_id>', methods=['DELETE'])
@token_required
def remove_from_pantry(current_user_id, pantry_id):
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database connection failed',
                'status': 'DB_ERROR'
            }), 503
        
        cur = conn.cursor()
        
        # Verify pantry item exists and belongs to user
        cur.execute(
            "SELECT * FROM usersProducts WHERE pantryID = %s AND userID = %s",
            (pantry_id, current_user_id)
        )
        pantry_item = cur.fetchone()
        
        if not pantry_item:
            cur.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Pantry item not found or does not belong to user',
                'status': 'NOT_FOUND'
            }), 404
        
        # Delete the pantry item
        cur.execute(
            "DELETE FROM usersProducts WHERE pantryID = %s",
            (pantry_id,)
        )
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Item removed from pantry'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Server error',
            'status': 'SERVER_ERROR',
            'details': str(e)
        }), 500

@pantry_bp.route('/pantry', methods=['GET'])
@token_required
def get_user_pantry(current_user_id):
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database connection failed',
                'status': 'DB_ERROR'
            }), 503
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all pantry items for the user with product details
        cur.execute("""
            SELECT up.*, p.productName, p.productBrand, p.productCategory, p.productImages
            FROM usersProducts up
            JOIN products p ON up.productUPC = p.productUPC
            WHERE up.userID = %s
            ORDER BY up.date_purchased DESC
        """, (current_user_id,))
        
        pantry_items = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'items': pantry_items
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Server error',
            'status': 'SERVER_ERROR',
            'details': str(e)
        }), 500

@pantry_bp.route('/pantry/product/<product_upc>', methods=['GET'])
@token_required
def get_pantry_item_by_upc(current_user_id, product_upc):
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database connection failed',
                'status': 'DB_ERROR'
            }), 503
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get pantry item for the user with specific UPC
        cur.execute("""
            SELECT up.*, p.productName, p.productBrand, p.productCategory, p.productImages
            FROM usersProducts up
            JOIN products p ON up.productUPC = p.productUPC
            WHERE up.userID = %s AND up.productUPC = %s
        """, (current_user_id, product_upc))
        
        pantry_item = cur.fetchone()
        cur.close()
        conn.close()
        
        if not pantry_item:
            return jsonify({
                'success': False,
                'error': 'Product not found in user pantry',
                'status': 'NOT_FOUND'
            }), 404
        
        return jsonify({
            'success': True,
            'pantry_item': pantry_item
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Server error',
            'status': 'SERVER_ERROR',
            'details': str(e)
        }), 500