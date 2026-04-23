async def _get_key_info(
        client: httpx.AsyncClient,
        org_id: str,
        keycloak_user_id: str,
    ) -> dict | None:
        from storage.user_store import UserStore

        if LITE_LLM_API_KEY is None or LITE_LLM_API_URL is None:
            logger.warning('LiteLLM API configuration not found')
            return None
        user = await UserStore.get_user_by_id(keycloak_user_id)
        if not user:
            return {}

        org_member = None
        for om in user.org_members:
            if om.org_id == org_id:
                org_member = om
                break
        if not org_member or not org_member.llm_api_key:
            return {}
        response = await client.get(
            f'{LITE_LLM_API_URL}/key/info?key={org_member.llm_api_key}'
        )
        response.raise_for_status()
        response_json = response.json()
        key_info = response_json.get('info')
        if not key_info:
            return {}
        return {
            'key_max_budget': key_info.get('max_budget'),
            'key_spend': key_info.get('spend'),
        }