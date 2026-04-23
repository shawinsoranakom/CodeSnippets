async def _async_migrate_func(
        self, old_major_version: int, old_minor_version: int, old_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Migrate to the new version."""
        if old_major_version == 1:
            # version 2.1 introduced in 2025.8
            migration.migrate_1_to_2(old_data)

        if old_major_version <= 2 and old_minor_version < 2:
            # version 2.2 introduced in 2025.9.2
            migration.migrate_2_1_to_2_2(old_data)

        if old_major_version <= 2 and old_minor_version < 3:
            # version 2.3 introduced in 2026.3
            migration.migrate_2_2_to_2_3(old_data)

        if old_major_version <= 2 and old_minor_version < 4:
            # version 2.4 introduced in 2026.5
            migration.migrate_2_3_to_2_4(old_data)

        return old_data