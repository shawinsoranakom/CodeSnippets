def __init__(self, get_response):
        if get_response is None:
            raise ValueError("get_response must be provided.")
        self.get_response = get_response
        # If get_response is a coroutine function, turns us into async mode so
        # a thread is not consumed during a whole request.
        self.async_mode = iscoroutinefunction(self.get_response)
        if self.async_mode:
            # Mark the class as async-capable, but do the actual switch inside
            # __call__ to avoid swapping out dunder methods.
            markcoroutinefunction(self)
        super().__init__()