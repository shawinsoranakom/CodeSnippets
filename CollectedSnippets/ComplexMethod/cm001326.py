def _build_evaluate_prompt(
        self,
        *,
        messages: list[ChatMessage],
        task: str,
        ai_profile: AIProfile,
        ai_directives: AIDirectives,
        commands: list[CompletionModelFunction],
        include_os_info: bool,
    ) -> ChatPrompt:
        """Build the evaluation phase prompt."""
        system_prompt, _ = self._build_system_prompt(
            ai_profile=ai_profile,
            ai_directives=ai_directives,
            commands=commands,
            include_os_info=include_os_info,
        )

        # Format candidates for evaluation
        candidates_text = "\n".join(
            f"{i + 1}. {c.thought}"
            + (f" → Action: {c.action_name}" if c.leads_to_action else "")
            for i, c in enumerate(self.pending_candidates)
        )

        current_path = ""
        if self.tree:
            path = self.tree.get_current_path_contents()
            if path:
                current_path = " → ".join(path)

        # Use categorical or numeric evaluation instruction
        if self.config.evaluation_mode == "categorical":
            evaluate_instruction = self.config.evaluate_categorical_instruction.format(
                task=task,
                current_path=current_path or "Starting point",
                candidates=candidates_text,
            )
            prefill = '[{"thought_index": 0, "evaluation": "'
        else:
            evaluate_instruction = self.config.evaluate_instruction.format(
                task=task,
                current_path=current_path or "Starting point",
                candidates=candidates_text,
            )
            prefill = '[{"thought_index":'

        return ChatPrompt(
            messages=[
                ChatMessage.system(system_prompt),
                ChatMessage.user(f'Task: """{task}"""'),
                *messages,
                ChatMessage.user(evaluate_instruction),
            ],
            prefill_response=prefill,
            functions=commands,
        )