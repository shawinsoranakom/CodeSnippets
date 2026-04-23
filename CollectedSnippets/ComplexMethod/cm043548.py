def update_runtime_choices(self):
        """Update runtime choices."""
        routines_directory = Path(session.user.preferences.export_directory, "routines")

        if session.prompt_session and session.settings.USE_PROMPT_TOOLKIT:
            # choices: dict = self.choices_default
            choices: dict = {c: {} for c in self.controller_choices}  # type: ignore

            self.ROUTINE_FILES = {
                filepath.name: filepath for filepath in routines_directory.rglob("*.openbb")  # type: ignore
            }
            self.ROUTINE_DEFAULT_FILES = {
                filepath.name: filepath  # type: ignore
                for filepath in Path(routines_directory / "hub" / "default").rglob(
                    "*.openbb"
                )
            }
            self.ROUTINE_PERSONAL_FILES = {
                filepath.name: filepath  # type: ignore
                for filepath in Path(routines_directory / "hub" / "personal").rglob(
                    "*.openbb"
                )
            }

            choices["exe"] = {
                "--file": {
                    filename: {} for filename in list(self.ROUTINE_FILES.keys())
                },
                "-f": "--file",
                "--example": None,
                "-e": "--example",
                "--input": None,
                "-i": "--input",
                "--url": None,
                "--help": None,
                "-h": "--help",
            }
            choices["record"] = {
                "--name": None,
                "-n": "--name",
                "--description": None,
                "-d": "--description",
                "--public": None,
                "-p": "--public",
                "--tag1": {c: None for c in constants.SCRIPT_TAGS},
                "--tag2": {c: None for c in constants.SCRIPT_TAGS},
                "--tag3": {c: None for c in constants.SCRIPT_TAGS},
                "--help": None,
                "-h": "--help",
            }
            choices["stop"] = {"--help": None, "-h": "--help"}
            choices["results"] = {
                "--help": None,
                "-h": "--help",
                "--export": {c: None for c in ["csv", "json", "xlsx", "png", "jpg"]},
                "--index": None,
                "--key": None,
                "--chart": None,
                "--sheet_name": None,
            }

            self.update_completer(choices)