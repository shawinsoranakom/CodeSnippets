async def update_creds(self, user_id: str, updated: Credentials) -> None:
        if updated.id in SYSTEM_CREDENTIAL_IDS:
            raise ValueError(
                f"System credential #{updated.id} cannot be updated directly"
            )
        async with await self.locked_user_integrations(user_id):
            persisted = await self._get_persisted_user_creds_unlocked(user_id)
            current = next((c for c in persisted if c.id == updated.id), None)
            if not current:
                raise ValueError(
                    f"Credentials with ID {updated.id} "
                    f"for user with ID {user_id} not found"
                )
            if current.is_managed:
                raise ValueError(
                    f"AutoGPT-managed credential #{updated.id} cannot be updated"
                )
            if type(current) is not type(updated):
                raise TypeError(
                    f"Can not update credentials with ID {updated.id} "
                    f"from type {type(current)} "
                    f"to type {type(updated)}"
                )

            # Ensure no scopes are removed when updating credentials
            if (
                isinstance(updated, OAuth2Credentials)
                and isinstance(current, OAuth2Credentials)
                and not set(updated.scopes).issuperset(current.scopes)
            ):
                raise ValueError(
                    f"Can not update credentials with ID {updated.id} "
                    f"and scopes {current.scopes} "
                    f"to more restrictive set of scopes {updated.scopes}"
                )

            # Update only persisted credentials — no side-effectful provisioning
            updated_credentials_list = [
                updated if c.id == updated.id else c for c in persisted
            ]
            await self._set_user_integration_creds(user_id, updated_credentials_list)