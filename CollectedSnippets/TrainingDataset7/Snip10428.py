def ask_auto_now_add_addition(self, field_name, model_name):
        """Adding an auto_now_add field to a model."""
        if not self.dry_run:
            choice = self._choice_input(
                f"It is impossible to add the field '{field_name}' with "
                f"'auto_now_add=True' to {model_name} without providing a "
                f"default. This is because the database needs something to "
                f"populate existing rows.\n",
                [
                    "Provide a one-off default now which will be set on all "
                    "existing rows",
                    "Quit and manually define a default value in models.py.",
                ],
            )
            if choice == 2:
                sys.exit(3)
            else:
                return self._ask_default(default="timezone.now")
        return None