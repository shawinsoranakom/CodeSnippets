async def update(self, filename: Path | str, dependencies: Set[Path | str], persist=True):
        """Update dependencies for a file asynchronously.

        :param filename: The filename or path.
        :param dependencies: The set of dependencies.
        :param persist: Whether to persist the changes immediately.
        """
        if persist:
            await self.load()

        root = self._filename.parent
        try:
            key = Path(filename).relative_to(root).as_posix()
        except ValueError:
            key = filename
        key = str(key)
        if dependencies:
            relative_paths = []
            for i in dependencies:
                try:
                    s = str(Path(i).relative_to(root).as_posix())
                except ValueError:
                    s = str(i)
                relative_paths.append(s)

            self._dependencies[key] = relative_paths
        elif key in self._dependencies:
            del self._dependencies[key]

        if persist:
            await self.save()