async def acount(self):
        """See Paginator.count()."""
        if self._cache_acount is not None:
            return self._cache_acount
        c = getattr(self.object_list, "acount", None)
        if (
            inspect.iscoroutinefunction(c)
            and not inspect.isbuiltin(c)
            and method_has_no_args(c)
        ):
            count = await c()
        else:
            count = len(self.object_list)

        self._cache_acount = count
        return count