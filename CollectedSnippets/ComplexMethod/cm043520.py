def editor_file_selector(
        self, input_path: Union[str, Path], init: bool = True
    ) -> List[str]:
        """
        Provides an interactive file selection interface using a .toml file.

        Parameters
        ----------
        input_path : Union[str, Path]
            The path where file selection is to be performed.
        init : bool, optional
            Indicates whether to initialize the .toml file with the file tree.

        Returns
        -------
        List[str]
            A list of strings representing the paths of selected files.
        """

        root_path = Path(input_path)
        tree_dict = {}
        toml_file = DiskMemory(metadata_path(input_path)).path / "file_selection.toml"
        # Define the toml file path

        # Initialize .toml file with file tree if in initial state
        if init:
            tree_dict = {x: "selected" for x in self.get_current_files(root_path)}

            s = toml.dumps({"files": tree_dict})

            # add comments on all lines that match = "selected"
            s = "\n".join(
                [
                    "# " + line if line.endswith(' = "selected"') else line
                    for line in s.split("\n")
                ]
            )
            # Write to the toml file
            with open(toml_file, "w") as f:
                f.write(self.COMMENT)
                f.write(self.LINTING_STRING)
                f.write(s)

        else:
            # Load existing files from the .toml configuration
            all_files = self.get_current_files(root_path)
            s = toml.dumps({"files": {x: "selected" for x in all_files}})

            # get linting status from the toml file
            with open(toml_file, "r") as file:
                linting_status = toml.load(file)
            if (
                "linting" in linting_status
                and linting_status["linting"].get("linting", "").lower() == "off"
            ):
                self.is_linting = False
                self.LINTING_STRING = '[linting]\n"linting" = "off"\n\n'
                print("\nLinting is disabled")

            with open(toml_file, "r") as file:
                selected_files = toml.load(file)

            lines = s.split("\n")
            s = "\n".join(
                lines[:1]
                + [
                    line
                    if line.split(" = ")[0].strip('"') in selected_files["files"]
                    else "# " + line
                    for line in lines[1:]
                ]
            )

            # Write the merged list back to the .toml for user review and modification
            with open(toml_file, "w") as file:
                file.write(self.COMMENT)  # Ensure to write the comment
                file.write(self.LINTING_STRING)
                file.write(s)

        print(
            "Please select and deselect (add # in front) files, save it, and close it to continue..."
        )
        self.open_with_default_editor(
            toml_file
        )  # Open the .toml file in the default editor for user modification
        return self.get_files_from_toml(
            input_path, toml_file
        )