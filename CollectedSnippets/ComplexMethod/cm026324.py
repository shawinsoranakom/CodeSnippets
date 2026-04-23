async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
        step_id: str = "user",
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {}

        if user_input is not None:
            LOGGER.debug("Source: %s", self.source)

            self._async_abort_entries_match(
                {
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_PORT: user_input[CONF_PORT],
                    CONF_BACKUP_LOCATION: user_input[CONF_BACKUP_LOCATION],
                }
            )

            if not user_input[CONF_BACKUP_LOCATION].startswith("/"):
                errors[CONF_BACKUP_LOCATION] = "backup_location_relative"
                return self.async_show_form(
                    step_id=step_id,
                    data_schema=self.add_suggested_values_to_schema(
                        DATA_SCHEMA, user_input
                    ),
                    description_placeholders=placeholders,
                    errors=errors,
                )

            try:
                # Validate auth input and save uploaded key file if provided
                user_input = await self._validate_auth_and_save_keyfile(user_input)

                # Create a session using your credentials
                user_config = SFTPConfigEntryData(
                    host=user_input[CONF_HOST],
                    port=user_input[CONF_PORT],
                    username=user_input[CONF_USERNAME],
                    password=user_input.get(CONF_PASSWORD),
                    private_key_file=user_input.get(CONF_PRIVATE_KEY_FILE),
                    backup_location=user_input[CONF_BACKUP_LOCATION],
                )

                placeholders["backup_location"] = user_config.backup_location

                # Raises:
                # - OSError, if host or port are not correct.
                # - SFTPStorageInvalidPrivateKey, if private key is not valid format.
                # - asyncssh.misc.PermissionDenied, if credentials are not correct.
                # - SFTPStorageMissingPasswordOrPkey, if password and private key are not provided.
                # - asyncssh.sftp.SFTPNoSuchFile, if directory does not exist.
                # - asyncssh.sftp.SFTPPermissionDenied, if we don't have access to said directory
                async with (
                    connect(
                        host=user_config.host,
                        port=user_config.port,
                        options=await self.hass.async_add_executor_job(
                            get_client_options, user_config
                        ),
                    ) as ssh,
                    ssh.start_sftp_client() as sftp,
                ):
                    await sftp.chdir(user_config.backup_location)
                    await sftp.listdir()

                LOGGER.debug(
                    "Will register SFTP Storage agent with user@host %s@%s",
                    user_config.host,
                    user_config.username,
                )

            except OSError as e:
                LOGGER.exception(e)
                placeholders["error_message"] = str(e)
                errors["base"] = "os_error"
            except SFTPStorageInvalidPrivateKey:
                errors["base"] = "invalid_key"
            except PermissionDenied as e:
                placeholders["error_message"] = str(e)
                errors["base"] = "permission_denied"
            except SFTPStorageMissingPasswordOrPkey:
                errors["base"] = "key_or_password_needed"
            except SFTPNoSuchFile:
                errors["base"] = "sftp_no_such_file"
            except SFTPPermissionDenied:
                errors["base"] = "sftp_permission_denied"
            except Exception as e:  # noqa: BLE001
                LOGGER.exception(e)
                placeholders["error_message"] = str(e)
                placeholders["exception"] = type(e).__name__
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"{user_config.username}@{user_config.host}",
                    data=user_input,
                )
            finally:
                # We remove the saved private key file if any error occurred.
                if errors and bool(user_input.get(CONF_PRIVATE_KEY_FILE)):
                    keyfile = Path(user_input[CONF_PRIVATE_KEY_FILE])
                    keyfile.unlink(missing_ok=True)
                    with suppress(OSError):
                        keyfile.parent.rmdir()

        if user_input:
            user_input.pop(CONF_PRIVATE_KEY_FILE, None)

        return self.async_show_form(
            step_id=step_id,
            data_schema=self.add_suggested_values_to_schema(DATA_SCHEMA, user_input),
            description_placeholders=placeholders,
            errors=errors,
        )