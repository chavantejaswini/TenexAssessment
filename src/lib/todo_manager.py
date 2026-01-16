from copy import copy
from uuid import UUID

from lib.models import Todo, TodoWithChildren


class TodoManager:
    _todo_list: list[Todo]

    def __init__(self):
        self._todo_list = []

    def add_todo(
        self, title: str, description: str, parent_uuid: UUID | None = None
    ) -> Todo:
        if parent_uuid and (self.try_get_todo_by_uuid(parent_uuid) is None):
            raise ValueError(f"Parent todo with uuid {parent_uuid} does not exist.")

        todo = Todo(title=title, description=description, parent_uuid=parent_uuid)

        self._todo_list.append(todo)
        return todo

    def try_get_todo_by_uuid(
        self, todo_uuid: UUID, with_children: bool = False
    ) -> Todo | TodoWithChildren | None:
        found_todo = None
        for todo in self._todo_list:
            if todo.uuid == todo_uuid:
                found_todo = todo

        if todo is None:
            return None

        if with_children:
            children = self.get_children(todo_uuid)
            todo_with_children = TodoWithChildren.model_validate(
                found_todo.model_dump()
            )
            todo_with_children.children.extend(children)
            return todo_with_children
        else:
            return found_todo.model_copy()

    def remove_todo(self, todo_uuid: UUID, remove_children: bool = False) -> bool:
        todo = self.try_get_todo_by_uuid(todo_uuid)
        if not todo:
            return False

        if remove_children:
            for todo_child_uuid in todo.children:
                self.remove_todo(todo_child_uuid)

        self._todo_list.remove(todo)
        return True

    def get_all_todos(self) -> list[Todo]:
        return copy(self._todo_list)

    def get_children(self, parent_uuid: UUID) -> list[UUID]:
        """Return the UUIDs of the direct children of the parent."""
        children = []
        for todo in self._todo_list:
            if todo.parent_uuid == parent_uuid:
                children.append(todo.uuid)
        return children

    def get_children_recursive(self, parent_uuid: UUID) -> list[UUID]:
        """Return a list of UUIDs of children and children's children, etc."""
        children = self.get_children(parent_uuid)
        all_descendants = list(children)
        for child_uuid in children:
            all_descendants.extend(self.get_children_recursive(child_uuid))
        return all_descendants
