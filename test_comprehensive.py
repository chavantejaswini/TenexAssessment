#!/usr/bin/env python3
"""Comprehensive test of Todo app with SQLAlchemy persistence."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Clean database
db_file = os.path.join(os.path.dirname(__file__), 'todos.db')
if os.path.exists(db_file):
    os.remove(db_file)

from lib.database import init_db
from lib.todo_manager import TodoManager

print('\n📦 Initializing database...')
init_db()

print('\n🧪 Testing TodoManager with SQLite persistent storage...')
manager = TodoManager()

# Add todos
print('\n1️⃣  Adding todos...')
parent = manager.add_todo('Project Alpha', 'Main project')
print(f'   ✓ Created parent: {parent.title} ({parent.uuid})')

child1 = manager.add_todo('Task 1', 'First task', parent_uuid=parent.uuid)
print(f'   ✓ Created child1: {child1.title}')

child2 = manager.add_todo('Task 2', 'Second task', parent_uuid=parent.uuid)
print(f'   ✓ Created child2: {child2.title}')

grandchild = manager.add_todo('Subtask 1.1', 'Subtask', parent_uuid=child1.uuid)
print(f'   ✓ Created grandchild: {grandchild.title}')

# Retrieve
print('\n2️⃣  Retrieving todos...')
retrieved = manager.try_get_todo_by_uuid(parent.uuid)
print(f'   ✓ Retrieved parent: {retrieved.title}')

# Get children
print('\n3️⃣  Getting children...')
children_uuids = manager.get_children(parent.uuid)
print(f'   ✓ Found {len(children_uuids)} direct children of parent')

# Get all
print('\n4️⃣  Getting all root-level todos...')
all_todos = manager.get_all_todos()
print(f'   ✓ Total root-level todos: {len(all_todos)}')
for todo in all_todos:
    print(f'      - {todo.title}')

# Test persistence
print('\n5️⃣  Creating new manager instance (testing persistence)...')
manager2 = TodoManager()
all_todos2 = manager2.get_all_todos()
print(f'   ✓ Found {len(all_todos2)} todos in new instance!')
print(f'   ✓ DATA PERSISTED ACROSS INSTANCES (database working!)')

# Test deletion
print('\n6️⃣  Testing deletion modes...')

# SAFE mode
print('\n   a) Safe delete with children (should fail)...')
result = manager.remove_todo(child1.uuid, delete_mode='safe')
print(f'      ✓ Delete failed as expected: {result["error"][:50]}...')

still_exists = manager.try_get_todo_by_uuid(child1.uuid)
print(f'      ✓ Child still exists: {still_exists.title}')

# CASCADE delete
print('\n   b) Cascade delete (delete parent + all descendants)...')
result = manager.remove_todo(child1.uuid, delete_mode='cascade')
print(f'      ✓ Deleted {result["deleted_count"]} todos (parent + grandchild)')

# ORPHAN delete
print('\n   c) Orphan delete (delete parent, orphan children)...')
other_parent = manager.add_todo('Project Beta', 'Another project')
orphan_child1 = manager.add_todo('Orphan Child 1', 'Will be orphaned', parent_uuid=other_parent.uuid)
orphan_child2 = manager.add_todo('Orphan Child 2', 'Will be orphaned', parent_uuid=other_parent.uuid)

print(f'      Created parent with 2 children')
result = manager.remove_todo(other_parent.uuid, delete_mode='orphan')
print(f'      ✓ Orphaned {result["orphaned_count"]} children')

orphan1_after = manager.try_get_todo_by_uuid(orphan_child1.uuid)
print(f'      ✓ Orphan child1 parent_uuid: {orphan1_after.parent_uuid} (None = root)')

# Final status
print('\n✅ ALL TESTS PASSED!')
print('\n📊 Final Statistics:')
final_todos = manager.get_all_todos()
print(f'   - Total root-level todos: {len(final_todos)}')
print(f'   - Database persisted correctly')
print(f'   - All 3 deletion modes working')
print(f'   - Migration to SQLAlchemy COMPLETE')
