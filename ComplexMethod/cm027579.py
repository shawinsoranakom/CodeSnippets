async def _async_migrate_func(
        self,
        old_major_version: int,
        old_minor_version: int,
        old_data: dict[str, list[dict[str, Any]]],
    ) -> AreasRegistryStoreData:
        """Migrate to the new version."""
        if old_major_version < 2:
            if old_minor_version < 2:
                # Version 1.2 implements migration and freezes the available keys
                for area in old_data["areas"]:
                    # Populate keys which were introduced before version 1.2
                    area.setdefault("picture", None)

            if old_minor_version < 3:
                # Version 1.3 adds aliases
                for area in old_data["areas"]:
                    area["aliases"] = []

            if old_minor_version < 4:
                # Version 1.4 adds icon
                for area in old_data["areas"]:
                    area["icon"] = None

            if old_minor_version < 5:
                # Version 1.5 adds floor_id
                for area in old_data["areas"]:
                    area["floor_id"] = None

            if old_minor_version < 6:
                # Version 1.6 adds labels
                for area in old_data["areas"]:
                    area["labels"] = []

            if old_minor_version < 7:
                # Version 1.7 adds created_at and modified_at
                created_at = utc_from_timestamp(0).isoformat()
                for area in old_data["areas"]:
                    area["created_at"] = area["modified_at"] = created_at

            if old_minor_version < 8:
                # Version 1.8 adds humidity_entity_id and temperature_entity_id
                for area in old_data["areas"]:
                    area["humidity_entity_id"] = None
                    area["temperature_entity_id"] = None

            if old_minor_version < 9:
                # Version 1.9 sorts the areas by name
                old_data["areas"] = sorted(
                    old_data["areas"],
                    key=lambda area: area["name"].casefold(),
                )

        if old_major_version > 1:
            raise NotImplementedError
        return old_data