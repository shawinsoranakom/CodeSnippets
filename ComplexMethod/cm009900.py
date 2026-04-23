def _list_indices(self) -> list[str]:
        all_indices = [
            index["index"] for index in self.database.cat.indices(format="json")
        ]

        if self.include_indices:
            all_indices = [i for i in all_indices if i in self.include_indices]
        if self.ignore_indices:
            all_indices = [i for i in all_indices if i not in self.ignore_indices]

        return all_indices