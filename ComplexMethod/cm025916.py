async def _async_validate_backblaze_connection(
        self, user_input: dict[str, Any]
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Validate Backblaze B2 credentials, bucket, capabilities, and prefix.

        Returns a tuple of (errors_dict, placeholders_dict).
        """
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {}

        info = InMemoryAccountInfo()
        b2_api = B2Api(info)

        def _authorize_and_get_bucket_sync() -> None:
            """Synchronously authorize the account and get the bucket by name.

            This function is run in the executor because b2sdk operations are blocking.
            """
            b2_api.authorize_account(
                BACKBLAZE_REALM,  # Use the defined realm constant
                user_input[CONF_KEY_ID],
                user_input[CONF_APPLICATION_KEY],
            )
            b2_api.get_bucket_by_name(user_input[CONF_BUCKET])

        try:
            await self.hass.async_add_executor_job(_authorize_and_get_bucket_sync)

            allowed = b2_api.account_info.get_allowed()

            # Check if allowed info is available
            if allowed is None or not allowed.get("capabilities"):
                errors["base"] = "invalid_capability"
                placeholders["missing_capabilities"] = ", ".join(
                    sorted(REQUIRED_CAPABILITIES)
                )
            else:
                # Check if all required capabilities are present
                current_caps = set(allowed["capabilities"])
                if not REQUIRED_CAPABILITIES.issubset(current_caps):
                    missing_caps = REQUIRED_CAPABILITIES - current_caps
                    _LOGGER.warning(
                        "Missing required Backblaze B2 capabilities for Key ID '%s': %s",
                        user_input[CONF_KEY_ID],
                        ", ".join(sorted(missing_caps)),
                    )
                    errors["base"] = "invalid_capability"
                    placeholders["missing_capabilities"] = ", ".join(
                        sorted(missing_caps)
                    )
                else:
                    # Only check prefix if capabilities are valid
                    configured_prefix: str = user_input[CONF_PREFIX]
                    allowed_prefix = allowed.get("namePrefix") or ""
                    # Ensure configured prefix starts with Backblaze B2's allowed prefix
                    if allowed_prefix and not configured_prefix.startswith(
                        allowed_prefix
                    ):
                        errors[CONF_PREFIX] = "invalid_prefix"
                        placeholders["allowed_prefix"] = allowed_prefix

        except exception.Unauthorized:
            _LOGGER.debug(
                "Backblaze B2 authentication failed for Key ID '%s'",
                user_input[CONF_KEY_ID],
            )
            errors["base"] = "invalid_credentials"
        except exception.RestrictedBucket as err:
            _LOGGER.debug(
                "Access to Backblaze B2 bucket '%s' is restricted: %s",
                user_input[CONF_BUCKET],
                err,
            )
            placeholders["restricted_bucket_name"] = err.bucket_name
            errors[CONF_BUCKET] = "restricted_bucket"
        except exception.NonExistentBucket:
            _LOGGER.debug(
                "Backblaze B2 bucket '%s' does not exist", user_input[CONF_BUCKET]
            )
            errors[CONF_BUCKET] = "invalid_bucket_name"
        except exception.BadRequest as err:
            _LOGGER.error(
                "Backblaze B2 API rejected the request for Key ID '%s': %s",
                user_input[CONF_KEY_ID],
                err,
            )
            errors["base"] = "bad_request"
            placeholders["error_message"] = str(err)
        except (
            exception.B2ConnectionError,
            exception.B2RequestTimeout,
            exception.ConnectionReset,
        ) as err:
            _LOGGER.error("Failed to connect to Backblaze B2: %s", err)
            errors["base"] = "cannot_connect"
        except exception.MissingAccountData:
            # This generally indicates an issue with how InMemoryAccountInfo is used
            _LOGGER.error(
                "Missing account data during Backblaze B2 authorization for Key ID '%s'",
                user_input[CONF_KEY_ID],
            )
            errors["base"] = "invalid_credentials"
        except Exception:
            _LOGGER.exception(
                "An unexpected error occurred during Backblaze B2 configuration for Key ID '%s'",
                user_input[CONF_KEY_ID],
            )
            errors["base"] = "unknown"

        return errors, placeholders