async def _ensure_initialized(self) -> None:
        """Ensure assistant and thread are created."""
        if self._assistant is None:
            if self._assistant_id:
                self._assistant = await self._client.beta.assistants.retrieve(assistant_id=self._assistant_id)  # type: ignore[reportDeprecated]
            else:
                self._assistant = await self._client.beta.assistants.create(  # type: ignore[reportDeprecated]
                    model=self._model,
                    description=self.description,
                    instructions=self._instructions,
                    tools=self._api_tools,
                    metadata=self._metadata,
                    response_format=self._response_format if self._response_format else NOT_GIVEN,  # type: ignore
                    temperature=self._temperature,
                    tool_resources=self._tool_resources if self._tool_resources else NOT_GIVEN,  # type: ignore
                    top_p=self._top_p,
                )

        if self._thread is None:
            if self._init_thread_id:
                self._thread = await self._client.beta.threads.retrieve(thread_id=self._init_thread_id)  # type: ignore[reportDeprecated]
            else:
                self._thread = await self._client.beta.threads.create()  # type: ignore[reportDeprecated]

        # Retrieve initial state only once
        if not self._initial_state_retrieved:
            await self._retrieve_initial_state()
            self._initial_state_retrieved = True