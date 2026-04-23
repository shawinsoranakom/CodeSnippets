def _build_conversation(
        self,
        app_conversation_info: AppConversationInfo | None,
        sandbox: SandboxInfo | None,
        conversation_info: ConversationInfo | None,
    ) -> AppConversation | None:
        if app_conversation_info is None:
            return None
        sandbox_status = sandbox.status if sandbox else SandboxStatus.MISSING
        execution_status = (
            conversation_info.execution_status if conversation_info else None
        )
        conversation_url = None
        session_api_key = None
        if sandbox and sandbox.exposed_urls:
            conversation_url = next(
                (
                    exposed_url.url
                    for exposed_url in sandbox.exposed_urls
                    if exposed_url.name == AGENT_SERVER
                ),
                None,
            )
            if conversation_url:
                conversation_url += f'/api/conversations/{app_conversation_info.id.hex}'
            session_api_key = sandbox.session_api_key

        return AppConversation(
            **app_conversation_info.model_dump(),
            sandbox_status=sandbox_status,
            execution_status=execution_status,
            conversation_url=conversation_url,
            session_api_key=session_api_key,
        )