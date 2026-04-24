import os
from fastapi import FastAPI, HTTPException, Depends
from bson import ObjectId
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from dotenv import load_dotenv

from database import users_collection, tasks_collection
from auth import hash_password, verify_password, create_access_token
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

security = HTTPBearer()

def serialize(task):
    return {
        "id": str(task["_id"]),
        "title": task["title"],
        "completed": task["completed"],
        "due_time":task["due_time"]
    }

# 🔐 Auth middleware
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["user_id"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
@app.get("/")
def serve_home():
    return FileResponse("static/login.html")
# 👤 Signup
@app.post("/signup")
def signup(data: dict):
    if users_collection.find_one({"email": data["email"]}):
        raise HTTPException(status_code=400, detail="User already exists")

    users_collection.insert_one({
        "email": data["email"],
        "password": hash_password(data["password"])
    })

    return {"message": "User created"}

# 🔑 Login
@app.post("/login")
def login(data: dict):
    user = users_collection.find_one({"email": data["email"]})
    if not user or not verify_password(data["password"], user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"user_id": str(user["_id"])})
    return {"access_token": token}

# 📋 Get Tasks (protected)
@app.get("/tasks")
def get_tasks(user_id: str = Depends(get_current_user)):
    tasks = tasks_collection.find({"userId": user_id})
    return [serialize(t) for t in tasks]

# ➕ Create Task
@app.post("/tasks")
def create_task(data: dict, user_id: str = Depends(get_current_user)):
    task = {
        "title": data["title"],
        "completed": False,
        "userId": user_id,
        "due_time": data.get("due_time")  # ISO string
    }
    tasks_collection.insert_one(task)
    return {"message": "Task created"}

# ✏️ Update Task
@app.patch("/tasks/{task_id}")
def update_task(task_id: str, completed: bool, user_id: str = Depends(get_current_user)):
    result = tasks_collection.update_one(
        {"_id": ObjectId(task_id), "userId": user_id},
        {"$set": {"completed": completed}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"message": "updated"}

# ❌ Delete Task
@app.delete("/tasks/{task_id}")
def delete_task(task_id: str, user_id: str = Depends(get_current_user)):
    result = tasks_collection.delete_one(
        {"_id": ObjectId(task_id), "userId": user_id}
    )

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"message": "deleted"}
