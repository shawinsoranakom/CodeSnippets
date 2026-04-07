async def wrapper():
                    result = await f()
                    return f"{result} appending {self.myattr}"