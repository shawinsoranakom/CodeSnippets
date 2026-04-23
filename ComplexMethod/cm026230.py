async def download_file(
        self,
        file_id: str,
        directory_path: str | None = None,
        file_name: str | None = None,
        context: Context | None = None,
        **kwargs: dict[str, Any],
    ) -> dict[str, JsonValueType]:
        """Download a file from Telegram."""
        if directory_path:
            try:
                raise_if_invalid_path(directory_path)
            except ValueError as err:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="invalid_directory_path",
                    translation_placeholders={"directory_path": directory_path},
                ) from err
        else:
            directory_path = self.hass.config.path(DOMAIN)

        if file_name:
            try:
                raise_if_invalid_filename(file_name)
            except ValueError as err:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="invalid_file_name",
                    translation_placeholders={"file_name": file_name},
                ) from err

        file: File = await self._send_msg(
            self.bot.get_file,
            None,
            file_id=file_id,
            context=context,
        )
        if not file.file_path:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="action_failed",
                translation_placeholders={
                    "error": "No file path returned from Telegram"
                },
            )
        if not file_name:
            file_name = os.path.basename(file.file_path)

        custom_path = os.path.join(directory_path, file_name)
        await self.hass.async_add_executor_job(
            self._prepare_download_directory, directory_path
        )
        _LOGGER.debug("Download file %s to %s", file_id, custom_path)
        try:
            file_content = await file.download_as_bytearray()
            await self.hass.async_add_executor_job(
                Path(custom_path).write_bytes, file_content
            )
        except (RuntimeError, OSError, TelegramError) as exc:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="action_failed",
                translation_placeholders={"error": str(exc)},
            ) from exc
        return {ATTR_FILE_PATH: custom_path}