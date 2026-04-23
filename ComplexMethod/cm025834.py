async def _async_migrate_func(
        self,
        old_major_version: int,
        old_minor_version: int,
        old_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Migrate to the new version."""
        data = old_data
        if old_major_version == 1:
            if old_minor_version < 3:
                # Version 1.2 bumped to 1.3 because 1.2 was changed several
                # times during development.
                # Version 1.3 adds per agent settings, configurable backup time
                # and custom days
                data["config"]["agents"] = {}
                data["config"]["schedule"]["time"] = None
                if (state := data["config"]["schedule"]["state"]) in ("daily", "never"):
                    data["config"]["schedule"]["days"] = []
                    data["config"]["schedule"]["recurrence"] = state
                else:
                    data["config"]["schedule"]["days"] = [state]
                    data["config"]["schedule"]["recurrence"] = "custom_days"
            if old_minor_version < 4:
                # Workaround for a bug in frontend which incorrectly set days to 0
                # instead of to None for unlimited retention.
                if data["config"]["retention"]["copies"] == 0:
                    data["config"]["retention"]["copies"] = None
                if data["config"]["retention"]["days"] == 0:
                    data["config"]["retention"]["days"] = None
            if old_minor_version < 5:
                # Version 1.5 adds automatic_backups_configured
                data["config"]["automatic_backups_configured"] = (
                    data["config"]["create_backup"]["password"] is not None
                )
            if old_minor_version < 6:
                # Version 1.6 adds agent retention settings
                for agent in data["config"]["agents"]:
                    data["config"]["agents"][agent]["retention"] = None
            if old_minor_version < 7:
                # Version 1.7 adds failing addons and folders
                for backup in data["backups"]:
                    backup["failed_addons"] = []
                    backup["failed_folders"] = []

        # Note: We allow reading data with major version 2 in which the unused key
        # data["config"]["schedule"]["state"] will be removed. The bump to 2 is
        # planned to happen after a 6 month quiet period with no minor version
        # changes.
        # Reject if major version is higher than _MAX_READABLE_VERSION.
        if old_major_version > self._MAX_READABLE_VERSION:
            raise NotImplementedError
        return data