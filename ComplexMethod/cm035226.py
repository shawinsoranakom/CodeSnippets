async def _get_sandbox_by_session_api_key_legacy(
        self, session_api_key: str
    ) -> Union[SandboxInfo, None]:
        """Legacy method to get sandbox by session API key via runtime API.

        This is the fallback for sandboxes created before the session_api_key_hash
        column was added. It calls the remote runtime API which is less efficient.
        """
        try:
            response = await self._send_runtime_api_request(
                'GET',
                '/list',
            )
            response.raise_for_status()
            content = response.json()
            for runtime in content['runtimes']:
                if session_api_key == runtime['session_api_key']:
                    query = await self._secure_select()
                    query = query.filter(
                        StoredRemoteSandbox.id == runtime.get('session_id')
                    )
                    result = await self.db_session.execute(query)
                    sandbox = result.scalar_one_or_none()
                    if sandbox is None:
                        raise ValueError('sandbox_not_found')
                    # Backfill the hash for future lookups (Auto committed at end of request)
                    sandbox.session_api_key_hash = _hash_session_api_key(
                        session_api_key
                    )
                    return self._to_sandbox_info(sandbox, runtime)
        except Exception:
            _logger.exception(
                'Error getting sandbox from session_api_key', stack_info=True
            )

        # Get all stored sandboxes for the current user
        stmt = await self._secure_select()
        result = await self.db_session.execute(stmt)
        stored_sandboxes = result.scalars().all()

        # Check each sandbox's runtime data for matching session_api_key
        for stored_sandbox in stored_sandboxes:
            try:
                runtime = await self._get_runtime(stored_sandbox.id)
                if runtime and runtime.get('session_api_key') == session_api_key:
                    # Backfill the hash for future lookups (Auto committed at end of request)
                    stored_sandbox.session_api_key_hash = _hash_session_api_key(
                        session_api_key
                    )
                    return self._to_sandbox_info(stored_sandbox, runtime)
            except Exception:
                # Continue checking other sandboxes if one fails
                continue

        return None