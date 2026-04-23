async def async_step_select_folder(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step to ask for the folder name."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                path = str(user_input[CONF_FOLDER_PATH]).lstrip("/")
                folder = await self.client.create_folder("root", path)
            except OneDriveException:
                self.logger.debug("Failed to create folder", exc_info=True)
                errors["base"] = "folder_creation_error"
            if not errors:
                title = (
                    f"{self.drive.owner.user.display_name}'s OneDrive ({self.drive.owner.user.email})"
                    if self.drive.owner
                    and self.drive.owner.user
                    and self.drive.owner.user.display_name
                    and self.drive.owner.user.email
                    else "OneDrive"
                )
                return self.async_create_entry(
                    title=title,
                    data={
                        **self._data,
                        CONF_FOLDER_ID: folder.id,
                        CONF_FOLDER_PATH: user_input[CONF_FOLDER_PATH],
                    },
                )

        return self.async_show_form(
            step_id="select_folder",
            data_schema=FOLDER_NAME_SCHEMA,
            errors=errors,
        )