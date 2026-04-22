def check_origin(self, origin: str) -> bool:
        """Set up CORS."""
        return super().check_origin(origin) or is_url_from_allowed_origins(origin)