from typing import Tuple, Dict
from flask import Flask, request, jsonify
from sqlalchemy import select, insert
from sqlalchemy.sql import exists
from database import SessionLocal
from models import Group, User, Receipt, Item, user_items, user_groups

from groups.routes import groups_blueprint
from users.routes import user_blueprint

app = Flask(__name__)
app.register_blueprint(groups_blueprint, url_prefix='/groups')
app.register_blueprint(user_blueprint, url_prefix='/user')

# ----- RECEIPT ---------------------------------------------------------------
@app.route('/receipts/view/<group_name>', methods=['GET'])
def get_receipts(group_name: str):
    
    session = SessionLocal()
    
    try:
        receipts = session.query(Receipt).join(Group).filter(Group.group_name == group_name).all()
    
        results = {
            "receipts": [
                {
                    "receipt_id": receipt.receipt_id,
                    "slot_time": receipt.slot_time,
                    "total_price": receipt.total_price,
                    "payment_card": receipt.payment_card,
                } 
                for receipt in receipts
            ]
        }
        
        return jsonify(results), 200
    
    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)}), 500
    
    finally:
        session.close()


@app.route('/receipts/new/<group_name>', methods=['POST'])
def add_receipt(group_name: str):
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
    
    try:
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
        
        # Find which group to add the receipt and construct the new receipt
        group = session.query(Group).filter_by(group_name=group_name).one_or_none()
        new_receipt = Receipt(receipt_id=receipt_id, slot_time=slot_time, total_price=total_price, group_id=group.group_id, payment_card=payment_card)
        # Add and flush to auto-generate the receipt id
        session.add(new_receipt)
        session.flush()
        
        # Add items to receipt one by one
        for item in items:
            name = item["name"]
            quantity = item["quantity"] if item["quantity"] != "" else None
            weight = item["weight"] if item["weight"] != "" else None
            item_price = item["price"]
            
            new_item = Item(name=name, receipt_id=receipt_id, quantity=quantity, weight=weight, price=item_price)
            # Add and flush here to auto-generate item_id needed for user-item associations
            session.add(new_item)
            session.flush()
                        
            # Initialise empty user-item associations
            print(group.users)
            for user in group.users:
                print(user.username)
                stmt = insert(user_items).values(
                    user_id=user.user_id,
                    item_id=new_item.item_id,
                    # Quantity and weight for a user set as null when a new receipt is uploaded
                    quantity=None,
                    weight=None
                )
                session.execute(stmt)
                
        session.add(new_receipt)
        session.commit()
        return jsonify({"status": "success"}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"status": "failed", "message": str(e)})
        
    finally:
        session.close()


@app.route('/receipts/update/user-items', methods=['POST'])
def update_users_items_association() -> Tuple[Dict, int]:
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


@app.route('/receipts/get/<int:receipt_id>', methods=['GET'])
def get_users_items_assocation(receipt_id):
    """
    Get existing user-item associations of a receipt in a JSON format:
    {
        "items": [
            {
                "item_id": 1,
                "name": "Broccoli",
                "quantity": 3,
                "weight": 0.8,
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
                "quantity": 4,
                "weight": 1.2,
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
    """

    session = SessionLocal()
    
    try:
        
        # Single query to obtain all item information within the receipt
        results = (session.query(Item.item_id, Item.name, Item.quantity, Item.weight, User.user_id, user_items.c.quantity, user_items.c.weight)
                   .join(user_items, Item.item_id == user_items.c.item_id)
                   .filter(Item.receipt_id == receipt_id)
                   .all())
        
        # Initiate empty dictionary to construct JSON response
        item_dict = {}
        
        for item_id, name, total_quantity, total_weight, user_id, quantity, weight in results:
            # Fill item information for the first time only 
            if item_id not in item_dict:
                item_dict[item_id] = {
                    "item_id": item_id,
                    "item_name": name,
                    "total_quantity": total_quantity,
                    "total_weight": total_weight,
                    "users": []
                }
            # One for each user
            user_data = {
                "user_id": user_id,
                "quantity": quantity,
                "weight": weight
            }
            item_dict[item_id]["users"].append(user_data)


        # Convert the dictionary to the required list format
        result = {"items": list(item_dict.values())}
        
        return jsonify(result), 200
    
    except Exception as e:
        session.rollback()
        return jsonify({"status": "failed", "message": str(e)}), 500
    
    finally:
        session.close()


if __name__ == '__main__':
    app.run(debug=True)
