def _resolve(self, name, create_if_missing=False, leaf_cls=None, check_exists=True):
        try:
            relative_path = self._relative_path(name)
            return self._root.resolve(
                relative_path,
                create_if_missing=create_if_missing,
                leaf_cls=leaf_cls,
                check_exists=check_exists,
            )
        except NotADirectoryError as exc:
            absolute_path = self.path(exc.filename)
            raise FileExistsError(f"{absolute_path} exists and is not a directory.")