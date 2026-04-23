def _subscribe(self, directory, name, expression):
        root, rel_path = self._watch_root(directory)
        # Only receive notifications of files changing, filtering out other
        # types like special files:
        # https://facebook.github.io/watchman/docs/type
        only_files_expression = [
            "allof",
            ["anyof", ["type", "f"], ["type", "l"]],
            expression,
        ]
        query = {
            "expression": only_files_expression,
            "fields": ["name"],
            "since": self._get_clock(root),
            "dedup_results": True,
        }
        if rel_path:
            query["relative_root"] = rel_path
        logger.debug(
            "Issuing watchman subscription %s, for root %s. Query: %s",
            name,
            root,
            query,
        )
        self.client.query("subscribe", root, name, query)