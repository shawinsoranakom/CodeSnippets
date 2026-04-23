def cache_key(self) -> DependencyCacheKey:
        scopes_for_cache = (
            tuple(sorted(set(self.oauth_scopes or []))) if self._uses_scopes else ()
        )
        return (
            self.call,
            scopes_for_cache,
            self.computed_scope or "",
        )