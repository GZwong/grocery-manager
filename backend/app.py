from typing import Tuple, Dict
from flask import Flask, request, jsonify
from sqlalchemy import select, insert
from sqlalchemy.sql import exists
from database import SessionLocal
from models import Group, User, Receipt, Item, user_items


app = Flask(__name__)

# ----- GROUP -----------------------------------------------------------------
@app.route('/groups', methods=['GET'])
def get_groups():
    """
    Get all available groups.
    """
    session = SessionLocal()
    groups = session.query(Group).all()

    return jsonify([{
        "id": group.group_id,
        "name": group.group_name,
        "description": group.description
    } for group in groups]), 200


@app.route('/groups', methods=['POST'])
def create_group():
    """
    Create a new group.
    """
    session = SessionLocal()
    data = request.json
    group_name = data.get('name')
    description = data.get('description')

    if not group_name:
        return jsonify({"status": "failed", "message": "Group name is required!"}), 400
    
    # Check if group already exists
    if session.query(Group).filter_by(group_name=group_name).first():
        return jsonify({"status": "failed", "message": "Group already exists!"}), 400
    
    # Create and add the new group
    new_group = Group(group_name=group_name, description=description)
    session.add(new_group)
    session.commit()
    session.close()
    return jsonify({"status": "success", "message": "Group created successfully!"}), 201


@app.route('/groups/<int:group_id>', methods=['PUT'])
def update_group(group_id: int):
    """
    Update a specific group.
    """
    data = request.json
    new_name = data.get('name')
    new_description = data.get('description')
    
    if not new_name and not new_description:
        return jsonify({"status": "failed", "message": "At least one field (name or description) is required!"}), 400

    session = SessionLocal()
    group = session.query(Group).filter_by(group_id=group_id).one_or_none()

    if not group:
        return jsonify({"status": "failed", "message": "Group not found!"}), 404
    
    if new_name:
        group.group_name = new_name
    if new_description:
        group.description = new_description

    session.commit()
    session.close()
    return jsonify({"status": "success", "message": "Group updated successfully!"}), 200


@app.route('/groups/<int:group_id>', methods=['DELETE'])
def delete_group(group_id: int):
    """
    Delete a specific group.
    """
    session = SessionLocal()
    group = session.query(Group).filter_by(group_id=group_id).one_or_none()

    if not group:
        return jsonify({"status": "failed", "message": "Group not found!"}), 404
    
    session.delete(group)
    session.commit()
    session.close()
    return jsonify({"status": "success", "message": "Group deleted successfully!"}), 200


# ----- USER ------------------------------------------------------------------
@app.route('/users', methods=['GET'])
def get_all_users():
    """
    Get the user_id and username of all users.
    
    Returns a JSON like object.
    """
    session = SessionLocal()
    users = session.query(User).all()
    
    return jsonify([{
        "user_id": user.user_id,
        "username": user.username
    } for user in users])
    

@app.route('/add-user', methods=['POST'])
def create_user():
    """
    Create a new general user.
    """
    session = SessionLocal()
    data = request.json
    username = data.get('username')
    
    # Checks if user exists - fail if exists
    user_exists = session.query(exists().where(User.username == username)).scalar()
    if user_exists:
        return jsonify({"status": "failed", "message": "User already exists!"}), 400
    
    # Create a new_user
    new_user = User(username=username)
    session.add(new_user)
    session.commit()
    session.close()
    return jsonify({"status": "success"}), 200


@app.route('/del-user/<int:user-id>', methods=['DELETE'])
def del_user(user_id: int):
    """
    Delete a user from the database given its user_id.
    """
    session = SessionLocal()
    
    try:
        # Checks if user exists - fail if not
        user = session.query(User).filter_by(user_id=user_id).one_or_none()
        if not user:
            return jsonify({"status": "failed", "message": "User does not exists!"}), 400
        
        session.delete(user)
        session.commit()
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)}), 500
    
    finally:
        session.close()
    

@app.route('/<int:group_id>/add-user', methods=['POST'])
def add_user_to_group(group_id):
    """
    Add an existing user to an existing group.
    """
    session = SessionLocal()
    
    try: 
        data = request.json
        username = data.get('username')
        
        # Checks if user and group exists
        group = session.query(Group).filter_by(group_id=group_id).one_or_none()
        user = session.query(User).filter_by(username=username).one_or_none()
        if not group and not user:
            return jsonify({"status": "failed", "message": "Group or user does not exist"}), 404
        
        # Checks if user is already in the group
        if user in group.users:
            return jsonify({"status": "failed", "message": "User is already in the group"}), 404
        
        # Let the user join the group
        group.users.append(user)
        session.commit()
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        session.rollback()
        return jsonify({"status": "failed", "message": str(e)}), 500

    finally:
        session.close()


@app.route('/<int:group_id>/<int:user_id>', methods=['DELETE'])
def del_user_from_group(group_id: int, user_id: int):
    """
    Delete a user from a group, given its user_id and group_id.
    """
    session = SessionLocal()
    
    try:
        user = session.query(User).filter_by(user_id=user_id).one_or_none()
        group = session.query(Group).filter_by(group_id=group_id).one_or_none()
        
        # Check if the user and group exist
        if not user or not group:
            return jsonify({"status": "failed", "message": "User or group does not exist, hence cannot be deleted."}), 404
        
        # Check if the user is in the group
        if group not in user.groups:
            return jsonify({"status": "failed", "message": "User not in the group!"}), 404
        
        # Remove the user from the group
        user.groups.remove(group)
        session.commit()
        
        return jsonify({"status": "success", "message": "User removed from the group!"}), 200
    
    except Exception as e:
        session.rollback()
        return jsonify({"status": "failed", "message": str(e)}), 500
    
    finally:
        session.close()
    
    
# ----- RECEIPT ---------------------------------------------------------------
@app.route('/<int:group_id>/add-receipt', methods=['POST'])
def add_receipt(group_id: int):
    """
    Adds a receipt to a group. Expects a JSON post in the form of:
        {
            "receipt_id": 323223,
            "slot_time": ,
            "items": [
                {"name": "Broccoli", "quantity": "", "weight", "0.86kg", "price": "2.19"},
                {"name": "Chicken Thigh 2kg", "quantity": "2", "weight", "", "price": "4.80"},
            ],
            "total_price": 6.99,
            "payment_card": 1234,
        }

    Args:
        group_id (int): Group ID in the database embedded within the URL.
    """
    
    # Obtain and parse data
    session = SessionLocal()
    data = request.json
    receipt_id = data.get('receipt_id')
    slot_time = data.get('slot_time')
    total_price = data.get('total_price')
    items = data.get('items')
    payment_card = data.get('payment_card')
    
    # Checks if receipt exists - stops if already exists
    receipt_exists = session.query(exists().where(Receipt.receipt_id == receipt_id)).scalar()
    if receipt_exists:
        return jsonify({"status": "failed", "message": "Receipt already exists"}), 400
    
    new_receipt = Receipt(receipt_id=receipt_id, slot_time=slot_time, total_price=total_price, group_id=group_id, payment_card=payment_card)
    
    # Add items to receipt one by one
    for item in items:
        name = item["name"]
        quantity = item["quantity"] if item["quantity"] != "" else None
        weight = item["weight"] if item["weight"] != "" else None
        item_price = item["price"]
        
        new_item = Item(name=name, receipt_id=receipt_id, quantity=quantity, weight=weight, price=item_price)
        new_receipt.items.append(new_item)
        
    session.add(new_receipt)
    session.commit()
    return jsonify({"status": "success"}), 200


@app.route('/user-items', methods=['POST'])
def add_items_to_user() -> Tuple[Dict, int]:
    """
    Add item(s) to user(s) or update existing associations. Expects a JSON-like object in the format:
    {
        "items": [
            {
                "item_id": 1,
                "name": "Broccoli",
                "users": [
                    {
                        "user_id": 101,
                        "quantity": 2,
                        "weight": 0.5
                    },
                    {
                        "user_id": 102,
                        "quantity": 1,
                        "weight": 0.3
                    }
                ]
            },
            {
                "item_id": 2,
                "name": "Chicken Thigh",
                "users": [
                    {
                        "user_id": 101,
                        "quantity": 4,
                        "weight": 1.2
                    },
                ]
            }
        ]
    }
    Returns:
        Tuple[Dict, int]: a (JSON) dictionary indicating the status and HTTP status code.
    """
    
    data = request.json
    if not data or "items" not in data:
        return jsonify({"status": "failed", "message": "Invalid input"}), 400
    
    session = SessionLocal()
    
    try:
        for item_data in data["items"]:
            item_id = item_data["item_id"]
            item_name = item_data["name"]
            users_data = item_data["users"]
            
            item = session.query(Item).filter_by(item_id=item_id).one_or_none()
            
            # Loop through each user associated with the item
            for user_data in users_data:
                user_id = user_data["user_id"]
                quantity = user_data["quantity"]
                weight = user_data["weight"]
                
                # Find the associated user and item entry
                user_item_association = session.query(user_items).filter_by(user_id=user_id, item_id=item_id).one_or_none()
                
                # Create association if haven't exist
                if not user_item_association:
                    stmt = insert(user_items).values(
                        user_id=user_id,
                        item_id=item_id,
                        quantity=quantity,
                        weight=weight
                    )
                    session.execute(stmt)
                
                # Only update the entry if existed
                else:
                    user_item_association.quantity = quantity if quantity else None
                    user_item_association.weight = weight if weight else None

        session.commit()
        return jsonify({"status": "success", "message": "User and item association updated."})
    
    except Exception as e:
        session.rollback()
        return jsonify({"status": "failed", "message": str(e)}), 500 
    finally:
        session.close()


@app.route('/receipts/<int:receipt_id>', methods=['GET'])
def get_items(receipt_id):

    session = SessionLocal()
    receipt = session.query(Receipt).filter_by(receipt_id=receipt_id).one_or_none()
    
    if receipt:
        items = session.query(Item).filter_by(receipt=receipt).all()  # Get all items associated with the receipt
        items_data = [{"id": item.item_id, "name": item.name, "quantity": item.quantity, "price": float(item.price)} for item in items]
        return jsonify({"items": items_data}), 200  # Return the list of items with a 200 OK status

    # If the receipt is not found, return 404
    return jsonify({"error": "Receipt not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
