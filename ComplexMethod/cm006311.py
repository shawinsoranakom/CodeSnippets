async def initialize_user_variables(self, user_id: UUID | str, session: AsyncSession) -> None:
        if not self.settings_service.settings.store_environment_variables:
            await logger.adebug("Skipping environment variable storage.")
            return

        # Import the provider mapping to set default_fields for known providers
        try:
            from lfx.base.models.unified_models import get_model_provider_metadata

            # Build var_to_provider from all variables in metadata (not just primary)
            var_to_provider = {}
            var_to_info = {}  # Maps variable_key to its full info (including is_secret)
            metadata = get_model_provider_metadata()
            for provider, meta in metadata.items():
                for var in meta.get("variables", []):
                    var_key = var.get("variable_key")
                    if var_key:
                        var_to_provider[var_key] = provider
                        var_to_info[var_key] = var
        except Exception:  # noqa: BLE001
            var_to_provider = {}
            var_to_info = {}

        for var_name in self.settings_service.settings.variables_to_get_from_environment:
            # Check if session is still usable before processing each variable
            if not session.is_active:
                await logger.awarning(
                    "Session is no longer active during variable initialization. "
                    "Some environment variables may not have been processed."
                )
                break

            if var_name in os.environ and os.environ[var_name].strip():
                value = os.environ[var_name].strip()

                # Skip placeholder/test values like "dummy" for API key variables only
                # This prevents test environments from overwriting user-configured model provider keys
                is_provider_variable = var_name in var_to_provider
                var_info = var_to_info.get(var_name, {})
                is_secret_variable = var_info.get("is_secret", False)

                if is_provider_variable and is_secret_variable and value.lower() == "dummy":
                    await logger.adebug(
                        f"Skipping API key variable {var_name} with placeholder value 'dummy' "
                        "to preserve user configuration"
                    )
                    continue

                query = select(Variable).where(Variable.user_id == user_id, Variable.name == var_name)
                # Set default_fields if this is a known provider variable
                default_fields = []
                try:
                    if is_provider_variable:
                        provider_name = var_to_provider[var_name]
                        # Get the variable type from metadata
                        var_display_name = var_info.get("variable_name", "api_key")

                        # Validate secret variables (API keys) before setting default_fields
                        # This prevents invalid keys from enabling providers during migration
                        if is_secret_variable:
                            try:
                                from lfx.base.models.unified_models import validate_model_provider_key

                                validate_model_provider_key(provider_name, {var_name: value})
                                # Only set default_fields if validation passes
                                default_fields = [provider_name, var_display_name]
                                await logger.adebug(f"Validated {var_name} - provider will be enabled")
                            except (ValueError, Exception) as validation_error:  # noqa: BLE001
                                # Validation failed - don't set default_fields
                                # This prevents the provider from appearing as "Enabled"
                                default_fields = []
                                await logger.adebug(
                                    f"Skipping default_fields for {var_name} - validation failed: {validation_error!s}"
                                )
                        else:
                            # Non-secret variables (like project_id, url) don't need validation
                            default_fields = [provider_name, var_display_name]
                            await logger.adebug(f"Set default_fields for non-secret variable {var_name}")
                    existing = (await session.exec(query)).first()
                except Exception as e:  # noqa: BLE001
                    await logger.aexception(f"Error querying {var_name} variable: {e!s}")
                    # If session got rolled back during query, stop processing
                    if not session.is_active:
                        await logger.awarning(
                            f"Session rolled back during {var_name} query. Stopping variable initialization."
                        )
                        break
                    continue

                try:
                    if existing:
                        # Check if the variable has been user-modified (updated_at != created_at)
                        # If so, don't overwrite with environment variable
                        is_user_modified = (
                            existing.updated_at is not None
                            and existing.created_at is not None
                            and existing.updated_at > existing.created_at
                        )

                        if is_user_modified:
                            # Variable was modified by user, don't overwrite with environment variable
                            # Only update default_fields if they're not set
                            if not existing.default_fields and default_fields:
                                variable_update = VariableUpdate(
                                    id=existing.id,
                                    default_fields=default_fields,
                                )
                                await self.update_variable_fields(
                                    user_id=user_id,
                                    variable_id=existing.id,
                                    variable=variable_update,
                                    session=session,
                                )
                            await logger.adebug(
                                f"Skipping update of user-modified variable {var_name} with environment value"
                            )
                        # Variable was not user-modified, safe to update from environment
                        elif not existing.default_fields and default_fields:
                            # Update both value and default_fields
                            variable_update = VariableUpdate(
                                id=existing.id,
                                value=value,
                                default_fields=default_fields,
                            )
                            await self.update_variable_fields(
                                user_id=user_id,
                                variable_id=existing.id,
                                variable=variable_update,
                                session=session,
                            )
                        else:
                            await self.update_variable(user_id, var_name, value, session=session)
                    else:
                        await self.create_variable(
                            user_id=user_id,
                            name=var_name,
                            value=value,
                            default_fields=default_fields,
                            type_=CREDENTIAL_TYPE,
                            session=session,
                        )
                    await logger.adebug(f"Processed {var_name} variable from environment.")
                except Exception as e:  # noqa: BLE001
                    await logger.aexception(f"Error processing {var_name} variable: {e!s}")
                    # If session got rolled back due to error, stop processing
                    if not session.is_active:
                        await logger.awarning(
                            f"Session rolled back after error processing {var_name}. Stopping variable initialization."
                        )
                        break