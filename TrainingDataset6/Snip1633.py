def decorator(func: DecoratedCallable) -> DecoratedCallable:
            self.add_middleware(BaseHTTPMiddleware, dispatch=func)  # ty: ignore[invalid-argument-type]
            return func