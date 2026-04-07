def add_question_mark(func):
            async def _wrapper(*args, **kwargs):
                await asyncio.sleep(0.01)
                return await func(*args, **kwargs) + "?"

            return _wrapper