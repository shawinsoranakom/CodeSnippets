async def delete_creds_by_id(self, user_id: str, credentials_id: str) -> None:
        if credentials_id in SYSTEM_CREDENTIAL_IDS:
            raise ValueError(f"System credential #{credentials_id} cannot be deleted")
        async with await self.locked_user_integrations(user_id):
            persisted = await self._get_persisted_user_creds_unlocked(user_id)
            target = next((c for c in persisted if c.id == credentials_id), None)
            if target and target.is_managed:
                raise ValueError(
                    f"AutoGPT-managed credential #{credentials_id} cannot be deleted"
                )
            filtered_credentials = [c for c in persisted if c.id != credentials_id]
            await self._set_user_integration_creds(user_id, filtered_credentials)