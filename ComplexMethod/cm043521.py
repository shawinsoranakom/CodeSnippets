def get_files_from_toml(
        self, input_path: Union[str, Path], toml_file: Union[str, Path]
    ) -> List[str]:
        """
        Retrieves a list of selected files from a .toml configuration file.

        Parameters
        ----------
        input_path : Union[str, Path]
            The path where file selection was performed.
        toml_file : Union[str, Path]
            The path to the .toml file containing the file selection.

        Returns
        -------
        List[str]
            A list of strings representing the paths of selected files.

        Raises
        ------
        Exception
            If no files are selected in the .toml file.
        """
        selected_files = []
        edited_tree = toml.load(toml_file)  # Load the edited .toml file

        # check if users have disabled linting or not
        if (
            "linting" in edited_tree
            and edited_tree["linting"].get("linting", "").lower() == "off"
        ):
            self.is_linting = False
            print("\nLinting is disabled")
        else:
            self.is_linting = True

        # Iterate through the files in the .toml and append selected files to the list
        for file, _ in edited_tree["files"].items():
            selected_files.append(file)

        # Ensure that at least one file is selected, or raise an exception
        if not selected_files:
            raise Exception(
                "No files were selected. Please select at least one file to proceed."
            )

        print(f"\nYou have selected the following files:\n{input_path}")

        project_path = Path(input_path).resolve()
        selected_paths = set(
            project_path.joinpath(file).resolve(strict=False) for file in selected_files
        )

        for displayable_path in DisplayablePath.make_tree(project_path):
            if displayable_path.path in selected_paths:
                p = displayable_path
                while p.parent and p.parent.path not in selected_paths:
                    selected_paths.add(p.parent.path)
                    p = p.parent

        try:
            for displayable_path in DisplayablePath.make_tree(project_path):
                if displayable_path.path in selected_paths:
                    print(displayable_path.displayable())

        except FileNotFoundError:
            print("Specified path does not exist: ", project_path)
        except Exception as e:
            print("An error occurred while trying to display the file tree:", e)

        print("\n")
        return selected_files