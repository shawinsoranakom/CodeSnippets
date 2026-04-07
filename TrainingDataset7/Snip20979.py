def __call__(self, f):
                async def wrapper():
                    result = await f()
                    return f"{result} appending {self.myattr}"

                return update_wrapper(wrapper, f)