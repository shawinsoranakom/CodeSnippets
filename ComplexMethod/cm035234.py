def _apply_server_agent_overrides(
        agent: Agent,
        agent_type: AgentType,
        mcp_config: dict,
        conversation_id: UUID,
        user_id: str | None,
    ) -> Agent:
        """Apply server-only fields that have no place in ``AgentSettings``.

        * System-prompt filename / kwargs (planning vs default agent).
        * LLM tracing metadata for SaaS analytics.
        """
        overrides: dict[str, Any] = {}
        if agent_type == AgentType.PLAN:
            overrides['system_prompt_filename'] = 'system_prompt_planning.j2'
            overrides['system_prompt_kwargs'] = {
                'plan_structure': format_plan_structure()
            }
        else:
            overrides['system_prompt_kwargs'] = {'cli_mode': False}

        # LLM tracing metadata for openhands/ models
        if should_set_litellm_extra_body(agent.llm.model):
            llm_metadata = get_llm_metadata(
                model_name=agent.llm.model,
                llm_type=agent.llm.usage_id or 'agent',
                conversation_id=conversation_id,
                user_id=user_id,
            )
            overrides['llm'] = agent.llm.model_copy(
                update={'litellm_extra_body': {'metadata': llm_metadata}}
            )

        # Condenser LLM tracing
        if agent.condenser is not None and hasattr(agent.condenser, 'llm'):
            condenser_llm = agent.condenser.llm
            condenser_updates: dict[str, Any] = {}
            if not condenser_llm.usage_id or condenser_llm.usage_id == 'agent':
                condenser_updates['usage_id'] = 'condenser'
            if should_set_litellm_extra_body(condenser_llm.model):
                condenser_metadata = get_llm_metadata(
                    model_name=condenser_llm.model,
                    llm_type='condenser',
                    conversation_id=conversation_id,
                    user_id=user_id,
                )
                condenser_updates['litellm_extra_body'] = {
                    'metadata': condenser_metadata
                }
            if condenser_updates:
                updated_condenser = agent.condenser.model_copy(
                    update={'llm': condenser_llm.model_copy(update=condenser_updates)}
                )
                overrides['condenser'] = updated_condenser

        return agent.model_copy(update=overrides)