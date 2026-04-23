async def get_conversation_skills(
    conversation_id: UUID,
    app_conversation_service: AppConversationService = (
        app_conversation_service_dependency
    ),
    sandbox_service: SandboxService = sandbox_service_dependency,
    sandbox_spec_service: SandboxSpecService = sandbox_spec_service_dependency,
) -> JSONResponse:
    """Get all skills associated with the conversation.

    This endpoint returns all skills that are loaded for the v1 conversation.
    Skills are loaded from multiple sources:
    - Sandbox skills (exposed URLs)
    - Global skills (OpenHands/skills/)
    - User skills (~/.openhands/skills/)
    - Organization skills (org/.openhands repository)
    - Repository skills (repo .agents/skills/, .openhands/microagents/, and legacy .openhands/skills/)

    Returns:
        JSONResponse: A JSON response containing the list of skills.
        Returns an empty list if the sandbox is not running.
    """
    try:
        # Get agent server context (conversation, sandbox, sandbox_spec, agent_server_url)
        ctx = await _get_agent_server_context(
            conversation_id,
            app_conversation_service,
            sandbox_service,
            sandbox_spec_service,
        )
        if isinstance(ctx, JSONResponse):
            return ctx
        if ctx is None:
            return JSONResponse(status_code=status.HTTP_200_OK, content={'skills': []})

        # Load skills from all sources
        logger.info(f'Loading skills for conversation {conversation_id}')

        # Prefer the shared loader to avoid duplication; otherwise return empty list.
        all_skills: list = []
        if isinstance(app_conversation_service, AppConversationServiceBase):
            project_dir = get_project_dir(
                ctx.sandbox_spec.working_dir, ctx.conversation.selected_repository
            )
            all_skills = await app_conversation_service.load_and_merge_all_skills(
                ctx.sandbox,
                ctx.conversation.selected_repository,
                project_dir,
                ctx.agent_server_url,
            )

        logger.info(
            f'Loaded {len(all_skills)} skills for conversation {conversation_id}: '
            f'{[s.name for s in all_skills]}'
        )

        # Transform skills to response format
        skills_response = []
        for skill in all_skills:
            # Determine type based on AgentSkills format and trigger
            skill_type: Literal['repo', 'knowledge', 'agentskills']
            if skill.is_agentskills_format:
                skill_type = 'agentskills'
            elif skill.trigger is None:
                skill_type = 'repo'
            else:
                skill_type = 'knowledge'

            # Extract triggers
            triggers: list[str] = []
            if isinstance(skill.trigger, (KeywordTrigger, TaskTrigger)):
                if hasattr(skill.trigger, 'keywords'):
                    triggers = skill.trigger.keywords
                elif hasattr(skill.trigger, 'triggers'):
                    triggers = skill.trigger.triggers

            skills_response.append(
                SkillResponse(
                    name=skill.name,
                    type=skill_type,
                    content=skill.content,
                    triggers=triggers,
                )
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'skills': [s.model_dump() for s in skills_response]},
        )

    except Exception as e:
        logger.error(f'Error getting skills for conversation {conversation_id}: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': f'Error getting skills: {str(e)}'},
        )