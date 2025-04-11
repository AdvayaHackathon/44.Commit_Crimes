from flask import Blueprint, request, jsonify, session
from app.core.database import get_db
from app.core.auth import create_user, authenticate_user, create_access_token
from datetime import timedelta

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.json
    
    # Validate required fields
    required_fields = ['username', 'email', 'password', 'role']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Validate role
    if data['role'] not in ['student', 'teacher']:
        return jsonify({"error": "Role must be either 'student' or 'teacher'"}), 400
    
    # Create user
    with get_db() as db:
        result = create_user(
            db=db,
            username=data['username'],
            email=data['email'],
            password=data['password'],
            full_name=data.get('full_name', ''),
            role=data['role']
        )
        
        if isinstance(result, dict) and 'error' in result:
            return jsonify(result), 400
        
        # Return user info (excluding password)
        return jsonify({
            "id": result.id,
            "username": result.username,
            "email": result.email,
            "full_name": result.full_name,
            "role": result.role,
            "message": "User registered successfully"
        }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login a user"""
    data = request.json
    
    # Validate required fields
    if 'username' not in data or 'password' not in data:
        return jsonify({"error": "Username and password are required"}), 400
    
    # Authenticate user
    with get_db() as db:
        user = authenticate_user(db, data['username'], data['password'])
        
        if not user:
            return jsonify({"error": "Invalid username or password"}), 401
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user.id},
            expires_delta=timedelta(minutes=60 * 24)  # 24 hours
        )
        
        # Store user info in session
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        
        return jsonify({
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username,
            "role": user.role
        }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout a user"""
    # Clear session
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current user info"""
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    return jsonify({
        "user_id": session['user_id'],
        "username": session['username'],
        "role": session['role']
    }), 200
