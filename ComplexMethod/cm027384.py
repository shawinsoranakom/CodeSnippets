async def async_step_init(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Manage the options."""
        errors = {}

        current_uuids = self.config_entry.options.get(CONF_ALLOW_NAMELESS_UUIDS, [])
        new_uuid = None

        if user_input is not None:
            if new_uuid := user_input.get("new_uuid", "").lower():
                try:
                    # accept non-standard formats that can be fixed by UUID
                    new_uuid = str(UUID(new_uuid))
                except ValueError:
                    errors["new_uuid"] = "invalid_uuid_format"

            if not errors:
                # don't modify current_uuids in memory, cause HA will think that the new
                # data is equal to the old, and will refuse to write them to disk.
                updated_uuids = user_input.get("allow_nameless_uuids", [])
                if new_uuid and new_uuid not in updated_uuids:
                    updated_uuids.append(new_uuid)

                data = {CONF_ALLOW_NAMELESS_UUIDS: list(updated_uuids)}
                return self.async_create_entry(title="", data=data)

        schema: VolDictType = {
            vol.Optional(
                "new_uuid",
                description={"suggested_value": new_uuid},
            ): str,
        }
        if current_uuids:
            schema |= {
                vol.Optional(
                    "allow_nameless_uuids",
                    default=current_uuids,
                ): cv.multi_select(sorted(current_uuids))
            }
        return self.async_show_form(
            step_id="init", errors=errors, data_schema=vol.Schema(schema)
        )