def is_in_memory_db(database_name):
        return not isinstance(database_name, Path) and (
            database_name == ":memory:" or "mode=memory" in database_name
        )