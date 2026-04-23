async def _resolve_provider_variables(self, provider: str) -> dict[str, str]:
        """Resolve all global variables for a provider using the async session.

        This avoids the run_until_complete thread dance by doing the lookup
        directly in the already-running async context.
        """
        result: dict[str, str] = {}
        provider_vars = get_provider_all_variables(provider)
        user_id = self._user_uuid
        if not provider_vars or not user_id:
            return result

        async with session_scope() as session:
            variable_service = get_variable_service()
            if variable_service is None:
                return result

            for var_info in provider_vars:
                var_key = var_info.get("variable_key")
                if not var_key:
                    continue
                try:
                    value = await variable_service.get_variable(
                        user_id=user_id,
                        name=var_key,
                        field="",
                        session=session,
                    )
                    if value and str(value).strip():
                        result[var_key] = str(value)
                except (ValueError, KeyError, AttributeError) as e:
                    logger.debug(f"Variable service lookup failed for '{var_key}', falling back to environment: {e}")
                    env_value = os.environ.get(var_key)
                    if env_value and env_value.strip():
                        result[var_key] = env_value
        return result