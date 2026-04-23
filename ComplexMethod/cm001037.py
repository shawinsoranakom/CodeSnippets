async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        provider: str = "",
        reason: str = "",
        scopes: list[str] | None = None,
        **kwargs: Any,
    ) -> ToolResponseBase:
        """Build and return a :class:`SetupRequirementsResponse` for the requested provider.

        Validates the *provider* slug against the known registry, merges any
        agent-requested OAuth *scopes* with the provider defaults, and constructs
        the credential setup card payload that the frontend renders as an inline
        authentication prompt.

        Returns an :class:`ErrorResponse` if *provider* is unknown.
        """
        _ = user_id  # setup card is user-agnostic; auth is enforced via requires_auth
        session_id = session.session_id if session else None
        provider = (provider or "").strip().lower()
        reason = (reason or "").strip()[:500]  # cap LLM-controlled text
        extra_scopes: list[str] = [
            str(s).strip() for s in (scopes or []) if str(s).strip()
        ]

        entry = SUPPORTED_PROVIDERS.get(provider)
        if not entry:
            supported = ", ".join(f"'{p}'" for p in SUPPORTED_PROVIDERS)
            return ErrorResponse(
                message=(
                    f"Unknown provider '{provider}'. Supported providers: {supported}."
                ),
                error="unknown_provider",
                session_id=session_id,
            )

        display_name: str = entry["name"]
        supported_types: list[str] = get_provider_auth_types(provider)
        # Merge agent-requested scopes with provider defaults (deduplicated, order preserved).
        default_scopes: list[str] = entry["default_scopes"]
        seen: set[str] = set()
        merged_scopes: list[str] = []
        for s in default_scopes + extra_scopes:
            if s not in seen:
                seen.add(s)
                merged_scopes.append(s)
        field_key = f"{provider}_credentials"

        message_parts = [
            f"To continue, please connect your {display_name} account.",
        ]
        if reason:
            message_parts.append(reason)

        credential_entry: _CredentialEntry = {
            "id": field_key,
            "title": f"{display_name} Credentials",
            "provider": provider,
            "types": supported_types,
            "scopes": merged_scopes,
        }
        missing_credentials: dict[str, _CredentialEntry] = {field_key: credential_entry}

        return SetupRequirementsResponse(
            type=ResponseType.SETUP_REQUIREMENTS,
            message=" ".join(message_parts),
            session_id=session_id,
            setup_info=SetupInfo(
                agent_id=f"connect_{provider}",
                agent_name=display_name,
                user_readiness=UserReadiness(
                    has_all_credentials=False,
                    missing_credentials=missing_credentials,
                    ready_to_run=False,
                ),
                requirements={
                    "credentials": [missing_credentials[field_key]],
                    "inputs": [],
                    "execution_modes": [],
                },
            ),
        )