def ask_not_null_addition(self, field_name, model_name):
        """Adding a NOT NULL field to a model."""
        if not self.dry_run:
            choice = self._choice_input(
                f"It is impossible to add a non-nullable field '{field_name}' "
                f"to {model_name} without specifying a default. This is "
                f"because the database needs something to populate existing "
                f"rows.\n"
                f"Please select a fix:",
                [
                    (
                        "Provide a one-off default now (will be set on all existing "
                        "rows with a null value for this column)"
                    ),
                    "Quit and manually define a default value in models.py.",
                ],
            )
            if choice == 2:
                sys.exit(3)
            else:
                return self._ask_default()
        return None