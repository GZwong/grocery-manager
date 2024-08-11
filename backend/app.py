from typing import Tuple, Dict
from flask import Flask, request, jsonify
from database import SessionLocal
from models import Group, User, Receipt, Item


app = Flask(__name__)


@app.route('/create-group', methods=['POST'])
def create_group():

    
    session = SessionLocal()
    data = request.json
    group_name = data.get('group_name')
    description = data.get('description')

    # Checks if group exists - fail if exists
    group_exists = session.query(Group).filter_by(group_name=group_name).one_or_none()
    if group_exists:
        return jsonify({"status": "failed"}), 400
    
    # Create a new group
    new_group = Group(group_name=group_name, description=description)
    session.add(new_group)
    session.commit()
    return jsonify({"status": "success"}), 200


# Add user


@app.route('/<int:group_id>/add-user', methods=['POST'])
def add_user_to_group(group_id):
    """Add an existing user to an existing group.

    Returns:
        _type_: _description_
    """
    
    session = SessionLocal()
    data = request.json
    group_name = data.get('group_name')
    username = data.get('username')
    
    # Checks if user and group exists
    group = session.query(Group).filter_by(group_name=group_name).one_or_none()
    user = session.query(User).filter_by(username=username).one_or_none()
    if not group and not user:
        return jsonify({"status": "failed", "message": "Group or user does not exist"}), 400
    
    # Checks if user is already in the group
    if user in group.users:
        return jsonify({"status": "failed", "message": "User is already in the group"}), 400
    
    # Let the user join the group
    group.users.append(user)
    session.commit()
    return jsonify({"status": "success"}), 200
    


@app.route('/add-item-to-user', methods=['POST'])
def add_item_to_user() -> Tuple[Dict, int]:
    """
    Add an item to a user. 

    Returns:
        Tuple[Dict, int]: a (JSON) dictionary indicating the status and HTTP status code.
    """
    session = SessionLocal()  # Kickstart a session instance
    data = request.json
    user_id = data.get('user_id')
    item_id = data.get('item_id')
    
    user = session.query(User).filter_by(user_id=user_id).one_or_none()
    item = session.query(Item).filter_by(item_id=item_id).one_or_none()
    
    if user and item:
        user.items.append(item)
        session.commit()
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "failed"}), 400


@app.route('/get-items-for-receipt/<int:receipt_id>', methods=['GET'])
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
