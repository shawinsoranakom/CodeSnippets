def run_and_clear_commit_hooks(self):
        self.validate_no_atomic_block()
        current_run_on_commit = self.run_on_commit
        self.run_on_commit = []
        while current_run_on_commit:
            _, func, robust = current_run_on_commit.pop(0)
            if robust:
                try:
                    func()
                except Exception as e:
                    name = getattr(func, "__qualname__", func)
                    logger.exception(
                        "Error calling %s in on_commit() during transaction (%s).",
                        name,
                        e,
                    )
            else:
                func()