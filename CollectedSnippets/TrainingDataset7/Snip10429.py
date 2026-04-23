def ask_unique_callable_default_addition(self, field_name, model_name):
        """Adding a unique field with a callable default."""
        if not self.dry_run:
            version = get_docs_version()
            choice = self._choice_input(
                f"Callable default on unique field {model_name}.{field_name} "
                f"will not generate unique values upon migrating.\n"
                f"Please choose how to proceed:\n",
                [
                    f"Continue making this migration as the first step in "
                    f"writing a manual migration to generate unique values "
                    f"described here: "
                    f"https://docs.djangoproject.com/en/{version}/howto/"
                    f"writing-migrations/#migrations-that-add-unique-fields.",
                    "Quit and edit field options in models.py.",
                ],
            )
            if choice == 2:
                sys.exit(3)
        return None