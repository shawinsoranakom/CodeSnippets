def ask_for_files(self, skip_file_selection=False) -> tuple[FilesDict, bool]:
        """
        Prompts the user to select files for context improvement.

        This method supports selection from the terminal or using a previously saved list.
        In test mode, it retrieves files from a predefined TOML configuration.

        Returns
        -------
        FilesDict
            A dictionary with file paths as keys and file contents as values.
        """

        if os.getenv("GPTE_TEST_MODE") or skip_file_selection:
            # In test mode, retrieve files from a predefined TOML configuration
            # also get from toml if skip_file_selector is active
            assert self.FILE_LIST_NAME in self.metadata_db
            selected_files = self.get_files_from_toml(self.project_path, self.toml_path)
        else:
            # Otherwise, use the editor file selector for interactive selection
            if self.FILE_LIST_NAME in self.metadata_db:
                print(
                    f"File list detected at {self.toml_path}. Edit or delete it if you want to select new files."
                )
                selected_files = self.editor_file_selector(self.project_path, False)
            else:
                selected_files = self.editor_file_selector(self.project_path, True)

        content_dict = {}
        for file_path in selected_files:
            # selected files contains paths that are relative to the project path
            try:
                # to open the file we need the path from the cwd
                with open(
                    Path(self.project_path) / file_path, "r", encoding="utf-8"
                ) as content:
                    content_dict[str(file_path)] = content.read()
            except FileNotFoundError:
                print(f"Warning: File not found {file_path}")
            except UnicodeDecodeError:
                print(f"Warning: File not UTF-8 encoded {file_path}, skipping")

        return FilesDict(content_dict), self.is_linting