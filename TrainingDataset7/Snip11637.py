def get_fallback_sql(self, compiler, connection):
        raise NotImplementedError(
            f"{self.__class__.__name__}.get_fallback_sql() must be implemented "
            f"for backends that don't have the supports_tuple_lookups feature enabled."
        )