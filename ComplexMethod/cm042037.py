def get_files(self, relative_path: Path | str, root_relative_path: Path | str = None, filter_ignored=True) -> List:
        """
        Retrieve a list of files in the specified relative path.

        The method returns a list of file paths relative to the current FileRepository.

        :param relative_path: The relative path within the repository.
        :type relative_path: Path or str
        :param root_relative_path: The root relative path within the repository.
        :type root_relative_path: Path or str
        :param filter_ignored: Flag to indicate whether to filter files based on .gitignore rules.
        :type filter_ignored: bool
        :return: A list of file paths in the specified directory.
        :rtype: List[str]
        """
        try:
            relative_path = Path(relative_path).relative_to(self.workdir)
        except ValueError:
            relative_path = Path(relative_path)

        if not root_relative_path:
            root_relative_path = Path(self.workdir) / relative_path
        files = []
        try:
            directory_path = Path(self.workdir) / relative_path
            if not directory_path.exists():
                return []
            for file_path in directory_path.iterdir():
                if not file_path.is_relative_to(root_relative_path):
                    continue
                if file_path.is_file():
                    rpath = file_path.relative_to(root_relative_path)
                    files.append(str(rpath))
                else:
                    subfolder_files = self.get_files(
                        relative_path=file_path, root_relative_path=root_relative_path, filter_ignored=False
                    )
                    files.extend(subfolder_files)
        except Exception as e:
            logger.error(f"Error: {e}")
        if not filter_ignored:
            return files
        filtered_files = self.filter_gitignore(filenames=files, root_relative_path=root_relative_path)
        return filtered_files