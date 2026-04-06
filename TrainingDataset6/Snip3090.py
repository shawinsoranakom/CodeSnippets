async def read_item():
    return {
        "id": uuid.uuid4(),
        "name": "Island In The Moon",
        "price": 12.99,
        "description": "A place to be playin' and havin' fun",
        "tags": ["breater"],
    }