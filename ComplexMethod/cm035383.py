def load(
        cls,
        path: Union[str, Path],
        microagent_dir: Path | None = None,
        file_content: str | None = None,
    ) -> 'BaseMicroagent':
        """Load a microagent from a markdown file with frontmatter.

        The agent's name is derived from its path relative to the microagent_dir.
        """
        path = Path(path) if isinstance(path, str) else path

        # Calculate derived name from relative path if microagent_dir is provided
        # Otherwise, we will rely on the name from metadata later
        derived_name = None
        if microagent_dir is not None:
            # Special handling for files which are not in microagent_dir
            derived_name = cls.PATH_TO_THIRD_PARTY_MICROAGENT_NAME.get(
                path.name.lower()
            ) or str(path.relative_to(microagent_dir).with_suffix(''))

        # Only load directly from path if file_content is not provided
        if file_content is None:
            with open(path) as f:
                file_content = f.read()

        # Legacy repo instructions are stored in .openhands_instructions
        if path.name == '.openhands_instructions':
            return RepoMicroagent(
                name='repo_legacy',
                content=file_content,
                metadata=MicroagentMetadata(name='repo_legacy'),
                source=str(path),
                type=MicroagentType.REPO_KNOWLEDGE,
            )

        # Handle third-party agent instruction files
        third_party_agent = cls._handle_third_party(path, file_content)
        if third_party_agent is not None:
            return third_party_agent

        file_io = io.StringIO(file_content)
        loaded = frontmatter.load(file_io)
        content = loaded.content

        # Handle case where there's no frontmatter or empty frontmatter
        metadata_dict = loaded.metadata or {}

        # Ensure version is always a string (YAML may parse numeric versions as integers)
        if 'version' in metadata_dict and not isinstance(metadata_dict['version'], str):
            metadata_dict['version'] = str(metadata_dict['version'])

        try:
            metadata = MicroagentMetadata(**metadata_dict)

            # Validate MCP tools configuration if present
            if metadata.mcp_tools and metadata.mcp_tools.mcpServers:
                from openhands.core.config.mcp_config import StdioMCPServer

                has_stdio = any(
                    isinstance(s, StdioMCPServer)
                    for s in metadata.mcp_tools.mcpServers.values()
                )
                has_non_stdio = any(
                    not isinstance(s, StdioMCPServer)
                    for s in metadata.mcp_tools.mcpServers.values()
                )
                if has_non_stdio:
                    logger.warning(
                        f'Microagent {metadata.name} has remote servers. Only stdio servers are currently supported.'
                    )
                if not has_stdio:
                    raise MicroagentValidationError(
                        f'Microagent {metadata.name} has MCP tools configuration but no stdio servers. '
                        'Only stdio servers are currently supported.'
                    )
        except Exception as e:
            # Provide more detailed error message for validation errors
            error_msg = f'Error validating microagent metadata in {path.name}: {str(e)}'
            if 'type' in metadata_dict and metadata_dict['type'] not in [
                t.value for t in MicroagentType
            ]:
                valid_types = ', '.join([f'"{t.value}"' for t in MicroagentType])
                error_msg += f'. Invalid "type" value: "{metadata_dict["type"]}". Valid types are: {valid_types}'
            raise MicroagentValidationError(error_msg) from e

        # Create appropriate subclass based on type
        subclass_map = {
            MicroagentType.KNOWLEDGE: KnowledgeMicroagent,
            MicroagentType.REPO_KNOWLEDGE: RepoMicroagent,
            MicroagentType.TASK: TaskMicroagent,
        }

        # Infer the agent type:
        # 1. If inputs exist -> TASK
        # 2. If triggers exist -> KNOWLEDGE
        # 3. Else (no triggers) -> REPO (always active)
        inferred_type: MicroagentType
        if metadata.inputs:
            inferred_type = MicroagentType.TASK
            # Add a trigger for the agent name if not already present
            trigger = f'/{metadata.name}'
            if not metadata.triggers or trigger not in metadata.triggers:
                if not metadata.triggers:
                    metadata.triggers = [trigger]
                else:
                    metadata.triggers.append(trigger)
        elif metadata.triggers:
            inferred_type = MicroagentType.KNOWLEDGE
        else:
            # No triggers, default to REPO
            # This handles cases where 'type' might be missing or defaulted by Pydantic
            inferred_type = MicroagentType.REPO_KNOWLEDGE

        if inferred_type not in subclass_map:
            # This should theoretically not happen with the logic above
            raise ValueError(f'Could not determine microagent type for: {path}')

        # Use derived_name if available (from relative path), otherwise fallback to metadata.name
        agent_name = derived_name if derived_name is not None else metadata.name

        agent_class = subclass_map[inferred_type]
        return agent_class(
            name=agent_name,
            content=content,
            metadata=metadata,
            source=str(path),
            type=inferred_type,
        )