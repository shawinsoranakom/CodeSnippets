def _get_error_for_engine(self, engine, modules):
        return Warning(
            f"'same_tags' is used for multiple template tag modules: {modules}",
            obj=engine,
            id="templates.W003",
        )