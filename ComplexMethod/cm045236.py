async def _ensure_initialized(self, create_new_thread: bool = False, create_new_agent: bool = False) -> None:
        """
        Ensure agent and thread are properly initialized before operations.

        This method ensures that both the Azure AI Agent and thread are created or retrieved
        from existing IDs. It also handles retrieving the initial state of an existing thread
        when needed.

        Args:
            create_new_thread (bool): When True, creates a new thread even if thread_id is provided
            create_new_agent (bool): When True, creates a new agent even if agent_id is provided

        Raises:
            ValueError: If agent or thread creation fails
        """
        if self._agent is None or create_new_agent:
            if self._agent_id and create_new_agent is False:
                self._agent = await self._project_client.agents.get_agent(agent_id=self._agent_id)
            else:
                self._agent = await self._project_client.agents.create_agent(
                    name=self.name,
                    model=self._deployment_name,
                    description=self.description,
                    instructions=self._instructions,
                    tools=self._api_tools,
                    metadata=self._metadata,
                    response_format=self._response_format if self._response_format else None,  # type: ignore
                    temperature=self._temperature,
                    tool_resources=self._tool_resources if self._tool_resources else None,  # type: ignore
                    top_p=self._top_p,
                )

        if self._thread is None or create_new_thread:
            if self._init_thread_id and create_new_thread is False:
                self._thread = await self._project_client.agents.threads.get(thread_id=self._init_thread_id)
                # Retrieve initial state only once
                if not self._initial_state_retrieved:
                    await self._retrieve_initial_state()
                    self._initial_state_retrieved = True
            else:
                self._thread = await self._project_client.agents.threads.create()