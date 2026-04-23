async def _get_all_creds_unlocked(self, user_id: str) -> list[Credentials]:
        """Return all credentials for *user_id*.

        **Caller must already hold ``locked_user_integrations(user_id)``.**
        """
        user_integrations = await self._get_user_integrations(user_id)
        all_credentials = list(user_integrations.credentials)

        # These will always be added
        all_credentials.append(ollama_credentials)

        # These will only be added if the API key is set
        if settings.secrets.revid_api_key:
            all_credentials.append(revid_credentials)
        if settings.secrets.ideogram_api_key:
            all_credentials.append(ideogram_credentials)
        if settings.secrets.groq_api_key:
            all_credentials.append(groq_credentials)
        if settings.secrets.replicate_api_key:
            all_credentials.append(replicate_credentials)
        if settings.secrets.openai_api_key:
            all_credentials.append(openai_credentials)
        if settings.secrets.aiml_api_key:
            all_credentials.append(aiml_api_credentials)
        if settings.secrets.anthropic_api_key:
            all_credentials.append(anthropic_credentials)
        if settings.secrets.did_api_key:
            all_credentials.append(did_credentials)
        if settings.secrets.jina_api_key:
            all_credentials.append(jina_credentials)
        if settings.secrets.unreal_speech_api_key:
            all_credentials.append(unreal_credentials)
        if settings.secrets.open_router_api_key:
            all_credentials.append(open_router_credentials)
        if settings.secrets.enrichlayer_api_key:
            all_credentials.append(enrichlayer_credentials)
        if settings.secrets.fal_api_key:
            all_credentials.append(fal_credentials)
        if settings.secrets.exa_api_key:
            all_credentials.append(exa_credentials)
        if settings.secrets.e2b_api_key:
            all_credentials.append(e2b_credentials)
        if settings.secrets.nvidia_api_key:
            all_credentials.append(nvidia_credentials)
        if settings.secrets.screenshotone_api_key:
            all_credentials.append(screenshotone_credentials)
        if settings.secrets.mem0_api_key:
            all_credentials.append(mem0_credentials)
        if settings.secrets.apollo_api_key:
            all_credentials.append(apollo_credentials)
        if settings.secrets.smartlead_api_key:
            all_credentials.append(smartlead_credentials)
        if settings.secrets.zerobounce_api_key:
            all_credentials.append(zerobounce_credentials)
        if settings.secrets.google_maps_api_key:
            all_credentials.append(google_maps_credentials)
        if settings.secrets.llama_api_key:
            all_credentials.append(llama_api_credentials)
        if settings.secrets.v0_api_key:
            all_credentials.append(v0_credentials)
        if (
            settings.secrets.webshare_proxy_username
            and settings.secrets.webshare_proxy_password
        ):
            all_credentials.append(webshare_proxy_credentials)
        if settings.secrets.openweathermap_api_key:
            all_credentials.append(openweathermap_credentials)
        if settings.secrets.elevenlabs_api_key:
            all_credentials.append(elevenlabs_credentials)
        return all_credentials