def create_agent_runnable(self):
        messages = []

        # Use local variable to avoid mutating component state on repeated calls
        effective_system_prompt = self.system_prompt or ""

        llm = self._get_llm()

        # Enhance prompt for IBM Granite models (they need explicit tool usage instructions)
        if is_granite_model(llm) and self.tools:
            effective_system_prompt = get_enhanced_system_prompt(effective_system_prompt, self.tools)
            # Store enhanced prompt for use in agent.py without mutating original
            self._effective_system_prompt = effective_system_prompt

        # Only include system message if system_prompt is provided and not empty
        if effective_system_prompt.strip():
            messages.append(("system", "{system_prompt}"))

        messages.extend(
            [
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

        prompt = ChatPromptTemplate.from_messages(messages)
        self.validate_tool_names()

        try:
            # Use IBM Granite-specific agent if detected
            # Other WatsonX models (Llama, Mistral, etc.) use default behavior
            if is_granite_model(llm) and self.tools:
                return create_granite_agent(llm, self.tools, prompt)

            # Default behavior for other models (including non-Granite WatsonX models)
            return create_tool_calling_agent(llm, self.tools or [], prompt)
        except NotImplementedError as e:
            message = f"{self.display_name} does not support tool calling. Please try using a compatible model."
            raise NotImplementedError(message) from e