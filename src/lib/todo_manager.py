"""
TodoManager with SQLAlchemy persistent storage.

This manager uses SQLite database for persistent storage instead of in-memory
storage. All CRUD operations go through SQLAlchemy ORM.

Database schema includes indexes for:
- parent_uuid: Hierarchical queries
- created_at: Time-based filtering
- (parent_uuid, title): Composite searches
"""

from uuid import UUID

from sqlalchemy.orm import Session

from lib.database import get_session, TodoModel
from lib.models import Todo, TodoWithChildren


class TodoManager:
    """
    Manages Todo items with SQLAlchemy persistent storage.
    
    All operations are atomic and persist to SQLite database.
    """

    def __init__(self, db_session: Session | None = None):
        """
        Initialize TodoManager with optional database session.
        
        Args:
            db_session: SQLAlchemy session. If None, creates a new one.
        """
        self.db: Session = db_session or get_session()

    def add_todo(
        self, title: str, description: str, parent_uuid: UUID | None = None
    ) -> Todo:
        """
        Add a new todo to the database.
        
        Args:
            title: Todo title
            description: Todo description
            parent_uuid: Optional parent UUID (for hierarchical todos)
        
        Returns:
            Todo object created
        
        Raises:
            ValueError: If parent_uuid references non-existent parent
        """
        # Validate parent exists
        if parent_uuid:
            parent = self.db.query(TodoModel).filter_by(uuid=parent_uuid).first()
            if not parent:
                raise ValueError(f"Parent todo with uuid {parent_uuid} does not exist.")

        # Create new todo
        from uuid import uuid4
        new_uuid = uuid4()
        todo_model = TodoModel(
            uuid=new_uuid,
            title=title,
            description=description,
            parent_uuid=parent_uuid,
        )

        self.db.add(todo_model)
        self.db.commit()
        self.db.refresh(todo_model)

        # Convert to Pydantic model
        return self._model_to_pydantic(todo_model)

    def try_get_todo_by_uuid(
        self, todo_uuid: UUID, with_children: bool = False
    ) -> Todo | TodoWithChildren | None:
        """
        Get a todo by UUID from database.
        
        Args:
            todo_uuid: UUID to search for
            with_children: If True, include children UUIDs
        
        Returns:
            Todo or TodoWithChildren object, or None if not found
        """
        todo_model = self.db.query(TodoModel).filter_by(uuid=todo_uuid).first()
        if not todo_model:
            return None

        if with_children:
            children_uuids = [child.uuid for child in todo_model.children]
            todo_dict = self._model_to_pydantic(todo_model).model_dump()
            todo_with_children = TodoWithChildren(**todo_dict)
            todo_with_children.children.extend(children_uuids)
            return todo_with_children
        else:
            return self._model_to_pydantic(todo_model)

    def remove_todo(self, todo_uuid: UUID, delete_mode: str = "safe") -> dict:
        """
        Remove a todo with specified deletion strategy.
        
        Args:
            todo_uuid: UUID of todo to delete
            delete_mode: One of "cascade", "orphan", or "safe"
                - "cascade": Delete parent and all descendants recursively
                - "orphan": Delete parent, set children to root-level
                - "safe": Error if parent has children
        
        Returns:
            dict with status, message, and deleted_count
        """
        todo_model = self.db.query(TodoModel).filter_by(uuid=todo_uuid).first()
        if not todo_model:
            return {"deleted": False, "error": f"Todo {todo_uuid} not found"}

        children = self.get_children(todo_uuid)

        if children and delete_mode == "safe":
            return {
                "deleted": False,
                "error": f"Cannot delete todo with {len(children)} child/children. Use delete_mode='cascade' or 'orphan'.",
                "children_count": len(children),
            }

        deleted_count = 1

        if delete_mode == "cascade":
            # Recursively delete all descendants
            descendants = self.get_children_recursive(todo_uuid)
            for descendant_uuid in descendants:
                descendant = self.db.query(TodoModel).filter_by(uuid=descendant_uuid).first()
                if descendant:
                    self.db.delete(descendant)
                    deleted_count += 1

        elif delete_mode == "orphan":
            # Make direct children root-level
            child_models = self.db.query(TodoModel).filter_by(parent_uuid=todo_uuid).all()
            for child_model in child_models:
                child_model.parent_uuid = None

        # Remove the parent todo
        self.db.delete(todo_model)
        self.db.commit()

        return {
            "deleted": True,
            "deleted_count": deleted_count,
            "mode": delete_mode,
            "orphaned_count": len(children) if delete_mode == "orphan" else 0,
        }

    def get_all_todos(self) -> list[Todo]:
        """
        Get all root-level todos from database.
        
        Returns:
            List of root-level todos
        """
        # Only return root-level todos (parent_uuid is None)
        todo_models = self.db.query(TodoModel).filter_by(parent_uuid=None).all()
        return [self._model_to_pydantic(model) for model in todo_models]

    def get_children(self, parent_uuid: UUID) -> list[UUID]:
        """
        Get direct children of a todo using indexed parent_uuid query.
        
        Args:
            parent_uuid: UUID of parent
        
        Returns:
            List of child UUIDs
        """
        children = self.db.query(TodoModel).filter_by(parent_uuid=parent_uuid).all()
        return [child.uuid for child in children]

    def get_children_recursive(self, parent_uuid: UUID) -> list[UUID]:
        """
        Get all descendants of a todo recursively.
        
        Args:
            parent_uuid: UUID of parent
        
        Returns:
            List of all descendant UUIDs (children, grandchildren, etc.)
        """
        children = self.get_children(parent_uuid)
        all_descendants = list(children)
        for child_uuid in children:
            all_descendants.extend(self.get_children_recursive(child_uuid))
        return all_descendants

    @staticmethod
    def _model_to_pydantic(todo_model: TodoModel) -> Todo:
        """Convert SQLAlchemy model to Pydantic Todo model."""
        return Todo(
            uuid=todo_model.uuid,
            title=todo_model.title,
            description=todo_model.description,
            parent_uuid=todo_model.parent_uuid,
        )
