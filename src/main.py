from typing import List, Literal
from uuid import UUID

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from lib.todo_manager import TodoManager
from lib.models import Todo, TodoWithChildren
from lib.database import init_db

# Initialize database on startup
init_db()

app = FastAPI()
manager = TodoManager()


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Todo App</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; }
            .container { width: 100%; max-width: 600px; background: white; border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); padding: 30px; }
            h1 { color: #333; margin-bottom: 30px; text-align: center; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; }
            input, textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-family: inherit; }
            textarea { resize: vertical; min-height: 80px; }
            button { width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: 600; transition: background 0.3s; }
            button:hover { background: #764ba2; }
            .todos-list { margin-top: 30px; }
            .todo-item { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: start; }
            .todo-content { flex: 1; }
            .todo-title { font-weight: 600; color: #333; margin-bottom: 5px; }
            .todo-desc { color: #777; font-size: 0.9em; }
            .delete-btn { background: #dc3545; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 0.85em; }
            .delete-btn:hover { background: #c82333; }
            .loading { text-align: center; color: #999; }
            .error { color: #dc3545; background: #f8d7da; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📝 Todo App</h1>
            <div id="error-message" class="error" style="display: none;"></div>
            
            <form id="todo-form">
                <div class="form-group">
                    <label>Title</label>
                    <input type="text" id="title" required placeholder="Enter todo title">
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <textarea id="description" placeholder="Enter todo description"></textarea>
                </div>
                <button type="submit">Add Todo</button>
            </form>

            <div class="todos-list">
                <h2 style="margin-bottom: 15px; color: #333;">Todos</h2>
                <div id="todos" class="loading">Loading todos...</div>
            </div>
        </div>

        <script>
            const API_BASE = 'http://localhost:8000';

            async function loadTodos() {
                try {
                    const response = await fetch(API_BASE + '/todo');
                    const todos = await response.json();
                    displayTodos(todos);
                } catch (error) {
                    console.error('Error loading todos:', error);
                    document.getElementById('todos').innerHTML = '<p class="error">Failed to load todos</p>';
                }
            }

            function displayTodos(todos) {
                const container = document.getElementById('todos');
                if (todos.length === 0) {
                    container.innerHTML = '<p style="color: #999; text-align: center;">No todos yet. Create one above!</p>';
                    return;
                }
                container.innerHTML = todos.map(todo => `
                    <div class="todo-item">
                        <div class="todo-content">
                            <div class="todo-title">${escapeHtml(todo.title)}</div>
                            <div class="todo-desc">${escapeHtml(todo.description)}</div>
                        </div>
                        <button class="delete-btn" onclick="deleteTodo('${todo.uuid}')">Delete</button>
                    </div>
                `).join('');
            }

            function escapeHtml(text) {
                const map = {
                    '&': '&amp;',
                    '<': '&lt;',
                    '>': '&gt;',
                    '"': '&quot;',
                    "'": '&#039;'
                };
                return text.replace(/[&<>"']/g, m => map[m]);
            }

            async function addTodo(e) {
                e.preventDefault();
                const title = document.getElementById('title').value;
                const description = document.getElementById('description').value;

                try {
                    const response = await fetch(API_BASE + '/todo?title=' + encodeURIComponent(title) + '&description=' + encodeURIComponent(description), {
                        method: 'POST'
                    });
                    const result = await response.json();
                    if (result.error) {
                        showError(result.error);
                    } else {
                        document.getElementById('todo-form').reset();
                        loadTodos();
                    }
                } catch (error) {
                    showError('Failed to add todo: ' + error.message);
                }
            }

            async function deleteTodo(uuid) {
                if (confirm('Are you sure you want to delete this todo?')) {
                    try {
                        await fetch(API_BASE + '/todo/' + uuid, { method: 'DELETE' });
                        loadTodos();
                    } catch (error) {
                        showError('Failed to delete todo: ' + error.message);
                    }
                }
            }

            function showError(message) {
                const errorDiv = document.getElementById('error-message');
                errorDiv.textContent = message;
                errorDiv.style.display = 'block';
                setTimeout(() => {
                    errorDiv.style.display = 'none';
                }, 5000);
            }

            document.getElementById('todo-form').addEventListener('submit', addTodo);
            loadTodos();
        </script>
    </body>
    </html>
    """


@app.get("/todo")
async def list_all_todos() -> List[Todo | TodoWithChildren]:
    """List all todos. Root-level todos include their direct children UUIDs."""
    all_todos = manager.get_all_todos()
    result = []
    
    for todo in all_todos:
        # Only include root-level todos (those without a parent)
        if todo.parent_uuid is None:
            children = manager.get_children(todo.uuid)
            if children:
                todo_with_children = TodoWithChildren.model_validate(todo.model_dump())
                todo_with_children.children.extend(children)
                result.append(todo_with_children)
            else:
                result.append(todo)
    
    return result


@app.get("/todo/{todo_uuid}")
async def get_todo(todo_uuid: UUID) -> Todo:
    return manager.try_get_todo_by_uuid(todo_uuid)


@app.post("/todo")
async def add_todo(
    title: str, description: str, parent_uuid: str = None
) -> Todo | dict:
    try:
        result = manager.add_todo(title, description, parent_uuid)
    except ValueError as e:
        return {"error": str(e)}
    return result


@app.delete("/todo/{todo_uuid}")
async def remove_todo(todo_uuid: str, delete_mode: str = "safe") -> dict:
    """
    Delete a todo with configurable deletion strategy.
    
    - delete_mode='safe' (default): Error if todo has children
    - delete_mode='cascade': Delete parent and all descendants
    - delete_mode='orphan': Delete parent, make children root-level
    """
    return manager.remove_todo(UUID(todo_uuid), delete_mode)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
