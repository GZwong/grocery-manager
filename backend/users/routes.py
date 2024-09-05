from typing import Tuple, Dict
from sqlalchemy import select, insert
from sqlalchemy.sql import exists
from flask import Blueprint, request, jsonify
from database import SessionLocal
from models import Group, User, Receipt, Item, user_items, user_groups

user_blueprint = Blueprint('user', __name__)

@user_blueprint.route("/get-all", methods=['GET'])
def get_all_users():
    """
    Get all user information.
    """
    try:
        session = SessionLocal()
        users = session.query(User).all()
    
        return jsonify([{
            "user_id": user.user_id,
            "username": user.username
        } for user in users]), 200
        
    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)}), 400
    
    finally:
        session.close()


@user_blueprint.route("/get/<int:user_id>", methods=['GET'])
def get_user(user_id:int):
    """
    Get information of a user given user_id.
    """
    try:
        session = SessionLocal()
        user = session.query(User).filter_by(user_id=user_id).one_or_none()
        
        return jsonify({
            "user_id": user.user_id,
            "username": user.username
        }), 200
        
    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)}), 400
    
    finally:
        session.close()


@user_blueprint.route("/create", methods=['POST'])
def create_new_user():
    """
    Create a new user. The expected JSON request should contain:
    {
        "username": "Example username"
    }
    """
    try:
        
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
    
    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)}), 400
    
    finally:
        session.close()


@user_blueprint.route("/delete", methods=['POST'])
def delete_user():
    """
    Delete a user from the database.
    """
    try:
        data = request.json
        user_id = data.get('user_id')
        
        session = SessionLocal()
        
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
