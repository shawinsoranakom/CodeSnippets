def ask_auto_now_add_addition(self, field_name, model_name):
        # We can't ask the user, so act like the user aborted.
        self.log_lack_of_migration(
            field_name,
            model_name,
            "it is impossible to add a field with 'auto_now_add=True' without "
            "specifying a default",
        )
        sys.exit(3)