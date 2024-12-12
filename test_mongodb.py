import asyncio
from fastapi import FastAPI
import motor.motor_asyncio  
from bson import ObjectId

# Used for debugging, remove when submitting!

client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017/")
db = client.get_database("ACSAMS")

user_collection = db.get_collection("users")

async def get_one():
    a = await user_collection.find_one()
    print(a)

async def get_many():
    async for item in user_collection.find():
        print(item)

async def search_user(search):
    a = await user_collection.find_one({"username":search})
    print(a)

app = FastAPI(
    title="test mongo",
    summary="mongodb",
)

@app.get("/get1")
async def get1():
    task = asyncio.create_task(get_one())
    await task

@app.get("/user/{name}")
async def get_user_by_name(name: str):
    task = asyncio.create_task(search_user(name))
    await task

@app.get("/getMany")
async def getMany():
    task = asyncio.create_task(get_many())
    await task