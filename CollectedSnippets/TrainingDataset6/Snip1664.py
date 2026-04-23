def computed_scope(self) -> str | None:
        if self.scope:
            return self.scope
        if self.is_gen_callable or self.is_async_gen_callable:
            return "request"
        return None