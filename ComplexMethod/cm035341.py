def _on_workspace_context_recall(
        self, event: RecallAction
    ) -> RecallObservation | None:
        """Add repository and runtime information to the stream as a RecallObservation.

        This method collects information from all available repo microagents and concatenates their contents.
        Multiple repo microagents are supported, and their contents will be concatenated with newlines between them.
        """
        # Create WORKSPACE_CONTEXT info:
        # - repository_info
        # - runtime_info
        # - repository_instructions
        # - microagent_knowledge

        # Collect raw repository instructions
        repo_instructions = ''

        # Retrieve the context of repo instructions from all repo microagents
        for microagent in self.repo_microagents.values():
            if repo_instructions:
                repo_instructions += '\n\n'
            repo_instructions += microagent.content

        # Find any matched microagents based on the query
        microagent_knowledge = self._find_microagent_knowledge(event.query)

        # Create observation if we have anything
        if (
            self.repository_info
            or self.runtime_info
            or repo_instructions
            or microagent_knowledge
            or self.conversation_instructions
        ):
            obs = RecallObservation(
                recall_type=RecallType.WORKSPACE_CONTEXT,
                repo_name=(
                    self.repository_info.repo_name
                    if self.repository_info
                    and self.repository_info.repo_name is not None
                    else ''
                ),
                repo_directory=(
                    self.repository_info.repo_directory
                    if self.repository_info
                    and self.repository_info.repo_directory is not None
                    else ''
                ),
                repo_branch=(
                    self.repository_info.branch_name
                    if self.repository_info
                    and self.repository_info.branch_name is not None
                    else ''
                ),
                repo_instructions=repo_instructions if repo_instructions else '',
                runtime_hosts=(
                    self.runtime_info.available_hosts
                    if self.runtime_info
                    and self.runtime_info.available_hosts is not None
                    else {}
                ),
                additional_agent_instructions=(
                    self.runtime_info.additional_agent_instructions
                    if self.runtime_info
                    and self.runtime_info.additional_agent_instructions is not None
                    else ''
                ),
                microagent_knowledge=microagent_knowledge,
                content='Added workspace context',
                date=self.runtime_info.date if self.runtime_info is not None else '',
                custom_secrets_descriptions=(
                    self.runtime_info.custom_secrets_descriptions
                    if self.runtime_info is not None
                    else {}
                ),
                conversation_instructions=(
                    self.conversation_instructions.content
                    if self.conversation_instructions is not None
                    else ''
                ),
                working_dir=self.runtime_info.working_dir if self.runtime_info else '',
            )
            return obs
        return None