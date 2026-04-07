def middleware(self, *args, **kwargs):
        from django.middleware.security import SecurityMiddleware

        return SecurityMiddleware(self.response(*args, **kwargs))