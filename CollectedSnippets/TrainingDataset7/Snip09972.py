def get_test_db_clone_settings(self, suffix):
        orig_settings_dict = self.connection.settings_dict
        source_database_name = orig_settings_dict["NAME"] or ":memory:"

        if not self.is_in_memory_db(source_database_name):
            root, ext = os.path.splitext(source_database_name)
            return {**orig_settings_dict, "NAME": f"{root}_{suffix}{ext}"}

        start_method = multiprocessing.get_start_method()
        if start_method == "fork":
            return orig_settings_dict
        if start_method in {"forkserver", "spawn"}:
            return {
                **orig_settings_dict,
                "NAME": f"{self.connection.alias}_{suffix}.sqlite3",
            }
        raise NotSupportedError(
            f"Cloning with start method {start_method!r} is not supported."
        )