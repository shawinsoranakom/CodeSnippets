def ask_not_null_alteration(self, field_name, model_name):
        """Changing a NULL field to NOT NULL."""
        if not self.dry_run:
            choice = self._choice_input(
                f"It is impossible to change a nullable field '{field_name}' "
                f"on {model_name} to non-nullable without providing a "
                f"default. This is because the database needs something to "
                f"populate existing rows.\n"
                f"Please select a fix:",
                [
                    (
                        "Provide a one-off default now (will be set on all existing "
                        "rows with a null value for this column)"
                    ),
                    "Ignore for now. Existing rows that contain NULL values "
                    "will have to be handled manually, for example with a "
                    "RunPython or RunSQL operation.",
                    "Quit and manually define a default value in models.py.",
                ],
            )
            if choice == 2:
                return NOT_PROVIDED
            elif choice == 3:
                sys.exit(3)
            else:
                return self._ask_default()
        return None