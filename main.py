from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from typing import List

app = FastAPI()


# Modèle Pydantic pour un livre
class Book(BaseModel):
    title: str
    author: str
    year: int


# Modèle Pydantic pour un livre avec ID
class BookInDB(Book):
    id: str


# Configuration de la connexion MongoDB
DATABASE_URL = "mongodb://mongodb:27017"
client = AsyncIOMotorClient(DATABASE_URL)
db = client.bookstore
collection = db.books


@app.get("/books", response_model=List[BookInDB])
async def get_books():
    books = await collection.find().to_list(1000)
    return [BookInDB(**book, id=str(book["_id"])) for book in books]


@app.get("/books/{book_id}", response_model=BookInDB)
async def get_book(book_id: str):
    book = await collection.find_one({"_id": ObjectId(book_id)})
    if book:
        return BookInDB(**book, id=str(book["_id"]))
    raise HTTPException(status_code=404, detail="Book not found")


@app.post("/books", response_model=BookInDB)
async def create_book(book: Book):
    new_book = await collection.insert_one(book.dict())
    created_book = await collection.find_one({"_id": new_book.inserted_id})
    return BookInDB(**created_book, id=str(created_book["_id"]))


@app.put("/books/{book_id}", response_model=BookInDB)
async def update_book(book_id: str, book: Book):
    updated_book = await collection.find_one_and_update(
        {"_id": ObjectId(book_id)},
        {"$set": book.dict()},
        return_document=True
    )
    if updated_book:
        return BookInDB(**updated_book, id=str(updated_book["_id"]))
    raise HTTPException(status_code=404, detail="Book not found")


@app.delete("/books/{book_id}")
async def delete_book(book_id: str):
    delete_result = await collection.delete_one({"_id": ObjectId(book_id)})
    if delete_result.deleted_count:
        return {"message": "Book deleted successfully"}
    raise HTTPException(status_code=404, detail="Book not found")