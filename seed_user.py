import sys
import os
import random
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

# Add parent dir to path so we can import from database
sys.path.insert(0, os.path.dirname(__file__))
from database.db import get_db

# Realistic USA names across regions
FIRST_NAMES = [
    "James", "Robert", "Michael", "William", "David",
    "Richard", "Joseph", "Thomas", "Charles", "Christopher",
    "Daniel", "Matthew", "Anthony", "Mark", "Donald",
    "Sarah", "Jessica", "Karen", "Nancy", "Lisa",
    "Betty", "Margaret", "Sandra", "Ashley", "Dorothy",
    "Emily", "Jennifer", "Maria", "Susan", "Michelle"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones",
    "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris",
    "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"
]

def generate_unique_user():
    """Generate a realistic user with unique email."""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)

    # Generate email from name with random 2-3 digit suffix
    suffix = random.randint(10, 999)
    email = f"{first_name.lower()}.{last_name.lower()}{suffix}@gmail.com"

    return {
        "name": f"{first_name} {last_name}",
        "email": email,
        "password": "password123"
    }

def seed_user():
    """Insert a unique user into the database."""
    conn = get_db()
    cursor = conn.cursor()

    # Try up to 10 times to find a unique email
    for attempt in range(10):
        user = generate_unique_user()

        # Check if email exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (user["email"],))
        if cursor.fetchone() is None:
            # Email is unique, insert user
            password_hash = generate_password_hash(user["password"])
            created_at = datetime.now().isoformat()

            cursor.execute(
                'INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)',
                (user["name"], user["email"], password_hash, created_at)
            )
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()

            print(f"User created successfully!")
            print(f"  ID: {user_id}")
            print(f"  Name: {user['name']}")
            print(f"  Email: {user['email']}")
            return

    conn.close()
    print("Failed to generate unique email after 10 attempts.")
    sys.exit(1)

if __name__ == "__main__":
    seed_user()
