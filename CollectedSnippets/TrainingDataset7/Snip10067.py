def _execute_with_wrappers(self, sql, params, many, executor):
        context = {"connection": self.db, "cursor": self}
        for wrapper in reversed(self.db.execute_wrappers):
            executor = functools.partial(wrapper, executor)
        return executor(sql, params, many, context)