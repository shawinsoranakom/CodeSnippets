def tree(self) -> _GDriveTree:
        match self.list_objects_strategy:
            case _ListObjectsStrategy.TreeTraversal:
                try:
                    items = self._traverse_objects_with_limit()
                except _ListObjectsLimitExceeded:
                    self.list_objects_strategy = _ListObjectsStrategy.FullScan
                    return self.tree()

            case _ListObjectsStrategy.FullScan:
                items = self._detect_objects_with_full_scan()

            case _ListObjectsStrategy.SingleObjectRequest:
                item = self._get(self.root)
                if item is None:
                    items = []
                elif item["mimeType"] != MIME_TYPE_FOLDER:
                    items = [item]
                else:
                    logging.error(
                        f"The object {self.root} is not expected to be a folder"
                    )
                    self.list_objects_strategy = _ListObjectsStrategy.TreeTraversal
                    return self.tree()

            case _:
                raise ValueError(
                    f"Unknown list objects strategy: {self.list_objects_strategy}"
                )

        items = self._apply_filters(items)
        items = [extend_metadata(file) for file in items]
        return _GDriveTree({file["id"]: file for file in items})