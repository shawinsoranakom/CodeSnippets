def log_lack_of_migration(self, field_name, model_name, reason):
        if self.verbosity > 0:
            self.log(
                f"Field '{field_name}' on model '{model_name}' not migrated: "
                f"{reason}."
            )