def _unpack_and_collect_files(self, files: list[BaseFile]) -> list[BaseFile]:
        """Recursively unpack bundles and collect files into BaseFile instances.

        Args:
            files (list[BaseFile]): List of BaseFile instances to process.

        Returns:
            list[BaseFile]: Updated list of BaseFile instances.
        """
        collected_files = []

        for file in files:
            path = file.path
            delete_after_processing = file.delete_after_processing
            data = file.data

            if path.is_dir():
                # Recurse into directories
                collected_files.extend(
                    [
                        BaseFileComponent.BaseFile(
                            data,
                            sub_path,
                            delete_after_processing=delete_after_processing,
                        )
                        for sub_path in path.rglob("*")
                        if sub_path.is_file()
                    ]
                )
            elif path.suffix[1:] in self.SUPPORTED_BUNDLE_EXTENSIONS:
                # Unpack supported bundles
                temp_dir = TemporaryDirectory()
                self._temp_dirs.append(temp_dir)
                temp_dir_path = Path(temp_dir.name)
                self._unpack_bundle(path, temp_dir_path)
                subpaths = list(temp_dir_path.iterdir())
                self.log(f"Unpacked bundle {path.name} into {subpaths}")
                collected_files.extend(
                    [
                        BaseFileComponent.BaseFile(
                            data,
                            sub_path,
                            delete_after_processing=delete_after_processing,
                        )
                        for sub_path in subpaths
                    ]
                )
            else:
                collected_files.append(file)

        # Recurse again if any directories or bundles are left in the list
        if any(
            file.path.is_dir() or file.path.suffix[1:] in self.SUPPORTED_BUNDLE_EXTENSIONS for file in collected_files
        ):
            return self._unpack_and_collect_files(collected_files)

        return collected_files