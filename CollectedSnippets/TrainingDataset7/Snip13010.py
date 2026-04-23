async def to_list(_iterator):
                as_list = []
                async for chunk in _iterator:
                    as_list.append(chunk)
                return as_list