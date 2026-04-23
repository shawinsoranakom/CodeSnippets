def get_current_files(self, project_path: Union[str, Path]) -> List[str]:
        """
        Generates a list of all files in the project directory. Will use .gitignore files if project_path is a git repository.

        Parameters
        ----------
        project_path : Union[str, Path]
            The path to the project directory.

        Returns
        -------
        List[str]
            A list of strings representing the relative paths of all files in the project directory.
        """
        all_files = []
        project_path = Path(
            project_path
        ).resolve()  # Ensure path is absolute and resolved

        file_list = project_path.glob("**/*")

        for path in file_list:  # Recursively list all files
            if path.is_file():
                relpath = path.relative_to(project_path)
                parts = relpath.parts
                if any(part.startswith(".") for part in parts):
                    continue  # Skip hidden files
                if any(part in self.IGNORE_FOLDERS for part in parts):
                    continue
                if relpath.name == "prompt":
                    continue  # Skip files named 'prompt'

                all_files.append(str(relpath))

        if is_git_repo(project_path) and "projects" not in project_path.parts:
            all_files = filter_by_gitignore(project_path, all_files)

        return sorted(all_files, key=lambda x: Path(x).as_posix())