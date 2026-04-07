def check_database_version_supported(self):
        """
        Raise an error if the database version isn't supported by this
        version of Django.
        """
        if (
            self.features.minimum_database_version is not None
            and self.get_database_version() < self.features.minimum_database_version
        ):
            db_version = ".".join(map(str, self.get_database_version()))
            min_db_version = ".".join(map(str, self.features.minimum_database_version))
            raise NotSupportedError(
                f"{self.display_name} {min_db_version} or later is required "
                f"(found {db_version})."
            )