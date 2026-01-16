#!/usr/bin/env python3
"""Quick test to verify database flow is working."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Clean up old database
db_file = os.path.join(os.path.dirname(__file__), 'todos.db')
if os.path.exists(db_file):
    os.remove(db_file)
    print("✓ Cleaned old database")

# Test imports
print("Testing imports...")
try:
    from lib.database import init_db
    print("✓ Imported init_db")
except Exception as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

try:
    from lib.todo_manager import TodoManager
    print("✓ Imported TodoManager")
except Exception as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

# Initialize database
print("\nInitializing database...")
try:
    init_db()
    print("✓ Database initialized")
except Exception as e:
    print(f"✗ Failed to init database: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test TodoManager
print("\nTesting TodoManager...")
try:
    manager = TodoManager()
    print("✓ Created TodoManager instance")
except Exception as e:
    print(f"✗ Failed to create TodoManager: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Add a todo
print("\nTesting add_todo...")
try:
    todo = manager.add_todo("Test Task", "A simple test")
    print(f"✓ Added todo: {todo.title} ({todo.uuid})")
except Exception as e:
    print(f"✗ Failed to add todo: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Retrieve todo
print("\nTesting retrieve...")
try:
    retrieved = manager.try_get_todo_by_uuid(todo.uuid)
    print(f"✓ Retrieved: {retrieved.title}")
except Exception as e:
    print(f"✗ Failed to retrieve: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Get all
print("\nTesting get_all_todos...")
try:
    all_todos = manager.get_all_todos()
    print(f"✓ Got {len(all_todos)} todos")
except Exception as e:
    print(f"✗ Failed to get all: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ All basic tests passed!")
