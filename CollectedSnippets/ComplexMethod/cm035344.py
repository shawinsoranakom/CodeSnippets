def _process_observation(
        self,
        obs: Observation,
        tool_call_id_to_message: dict[str, Message],
        max_message_chars: int | None = None,
        vision_is_active: bool = False,
        enable_som_visual_browsing: bool = False,
        current_index: int = 0,
        events: list[Event] | None = None,
    ) -> list[Message]:
        """Converts an observation into a message format that can be sent to the LLM.

        This method handles different types of observations and formats them appropriately:
        - CmdOutputObservation: Formats command execution results with exit codes
        - IPythonRunCellObservation: Formats IPython cell execution results, replacing base64 images
        - FileEditObservation: Formats file editing results
        - FileReadObservation: Formats file reading results from openhands-aci
        - AgentDelegateObservation: Formats results from delegated agent tasks
        - ErrorObservation: Formats error messages from failed actions
        - UserRejectObservation: Formats user rejection messages
        - FileDownloadObservation: Formats the result of a browsing action that opened/downloaded a file

        In function calling mode, observations with tool_call_metadata are stored in
        tool_call_id_to_message for later processing instead of being returned immediately.

        Args:
            obs: The observation to convert
            tool_call_id_to_message: Dictionary mapping tool call IDs to their corresponding messages (used in function calling mode)
            max_message_chars: The maximum number of characters in the content of an observation included in the prompt to the LLM
            vision_is_active: Whether vision is active in the LLM. If True, image URLs will be included
            enable_som_visual_browsing: Whether to enable visual browsing for the SOM model
            current_index: The index of the current event in the events list (for deduplication)
            events: The list of all events (for deduplication)

        Returns:
            list[Message]: A list containing the formatted message(s) for the observation.
                May be empty if the observation is handled as a tool response in function calling mode.

        Raises:
            ValueError: If the observation type is unknown
        """
        message: Message

        if isinstance(obs, CmdOutputObservation):
            # Note: CmdOutputObservation content is already truncated at initialization,
            # and the observation content should not have been modified after initialization
            # we keep this truncation for backwards compatibility for a time
            if obs.tool_call_metadata is None:
                # if it doesn't have tool call metadata, it was triggered by a user action
                text = truncate_content(
                    f'\nObserved result of command executed by user:\n{obs.to_agent_observation()}',
                    max_message_chars,
                )
            else:
                text = truncate_content(obs.to_agent_observation(), max_message_chars)
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, MCPObservation):
            # logger.warning(f'MCPObservation: {obs}')
            text = truncate_content(obs.content, max_message_chars)
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, IPythonRunCellObservation):
            text = obs.content
            # Clean up any remaining base64 images in text content
            splitted = text.split('\n')
            for i, line in enumerate(splitted):
                if '![image](data:image/png;base64,' in line:
                    splitted[i] = (
                        '![image](data:image/png;base64, ...) already displayed to user'
                    )
            text = '\n'.join(splitted)
            text = truncate_content(text, max_message_chars)

            # Create message content with text
            content: list[TextContent | ImageContent] = [TextContent(text=text)]

            # Add image URLs if available
            if obs.image_urls:
                # Filter out empty or invalid image URLs
                valid_image_urls = [
                    url for url in obs.image_urls if self._is_valid_image_url(url)
                ]
                invalid_count = len(obs.image_urls) - len(valid_image_urls)

                if valid_image_urls:
                    content.append(ImageContent(image_urls=valid_image_urls))
                    # Only add explanatory text if vision is active
                    if vision_is_active and invalid_count > 0:
                        # Add text indicating some images were filtered
                        content[
                            0
                        ].text += f'\n\nNote: {invalid_count} invalid or empty image(s) were filtered from this output. The agent may need to use alternative methods to access visual information.'  # type: ignore[union-attr]
                else:
                    logger.debug(
                        'IPython observation has image URLs but none are valid'
                    )
                    # Only add explanatory text if vision is active
                    if vision_is_active:
                        # Add text indicating all images were filtered
                        content[
                            0
                        ].text += f'\n\nNote: All {len(obs.image_urls)} image(s) in this output were invalid or empty and have been filtered. The agent should use alternative methods to access visual information.'  # type: ignore[union-attr]

            message = Message(role='user', content=content)
        elif isinstance(obs, FileEditObservation):
            text = truncate_content(str(obs), max_message_chars)
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, FileReadObservation):
            message = Message(
                role='user', content=[TextContent(text=obs.content)]
            )  # Content is already truncated by openhands-aci
        elif isinstance(obs, BrowserOutputObservation):
            text = obs.content
            content = [TextContent(text=text)]
            if (
                obs.trigger_by_action == ActionType.BROWSE_INTERACTIVE
                and enable_som_visual_browsing
            ):
                # Only add descriptive text if vision is active
                if vision_is_active:
                    # We know content[0] is TextContent since we just created it above
                    text_content = content[0]
                    assert isinstance(text_content, TextContent)
                    text_content.text += 'Image: Current webpage screenshot (Note that only visible portion of webpage is present in the screenshot. However, the Accessibility tree contains information from the entire webpage.)\n'

                # Determine which image to use and validate it
                image_url = None
                image_type = None
                if obs.set_of_marks is not None and len(obs.set_of_marks) > 0:
                    image_url = obs.set_of_marks
                    image_type = 'set of marks'
                elif obs.screenshot is not None and len(obs.screenshot) > 0:
                    image_url = obs.screenshot
                    image_type = 'screenshot'

                # Always add ImageContent if we have a valid image URL
                if self._is_valid_image_url(image_url):
                    content.append(ImageContent(image_urls=[image_url]))  # type: ignore[list-item]
                    logger.debug(f'Adding {image_type} for browsing')
                else:
                    if vision_is_active and image_url:
                        logger.warning(
                            f'Invalid image URL format for {image_type}: {image_url[:50]}...'
                        )
                        # Add text indicating the image was filtered (only if vision is active)
                        content[
                            0
                        ].text += f'\n\nNote: The {image_type} for this webpage was invalid or empty and has been filtered. The agent should use alternative methods to access visual information about the webpage.'  # type: ignore[union-attr]
                    elif vision_is_active and not image_url:
                        logger.debug(
                            'Vision enabled for browsing, but no valid image available'
                        )
                        # Add text indicating no image was available (only if vision is active)
                        content[
                            0
                        ].text += '\n\nNote: No visual information (screenshot or set of marks) is available for this webpage. The agent should rely on the text content above.'  # type: ignore[union-attr]

            message = Message(role='user', content=content)
        elif isinstance(obs, AgentDelegateObservation):
            text = truncate_content(
                obs.outputs.get('content', obs.content),
                max_message_chars,
            )
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, AgentThinkObservation):
            text = truncate_content(obs.content, max_message_chars)
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, TaskTrackingObservation):
            text = truncate_content(obs.content, max_message_chars)
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, ErrorObservation):
            text = truncate_content(obs.content, max_message_chars)
            text += '\n[Error occurred in processing last action]'
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, UserRejectObservation):
            text = 'OBSERVATION:\n' + truncate_content(obs.content, max_message_chars)
            text += '\n[Last action has been rejected by the user]'
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, AgentCondensationObservation):
            text = truncate_content(obs.content, max_message_chars)
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, FileDownloadObservation):
            text = truncate_content(obs.content, max_message_chars)
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, LoopDetectionObservation):
            # LoopRecovery should not be observed by llm, handled internally.
            return []
        elif (
            isinstance(obs, RecallObservation)
            and self.agent_config.enable_prompt_extensions
        ):
            if obs.recall_type == RecallType.WORKSPACE_CONTEXT:
                # everything is optional, check if they are present
                if obs.repo_name or obs.repo_directory:
                    repo_info = RepositoryInfo(
                        repo_name=obs.repo_name or '',
                        repo_directory=obs.repo_directory or '',
                        branch_name=obs.repo_branch or None,
                    )
                else:
                    repo_info = None

                date = obs.date

                if obs.runtime_hosts or obs.additional_agent_instructions:
                    runtime_info = RuntimeInfo(
                        available_hosts=obs.runtime_hosts,
                        additional_agent_instructions=obs.additional_agent_instructions,
                        date=date,
                        custom_secrets_descriptions=obs.custom_secrets_descriptions,
                        working_dir=obs.working_dir,
                    )
                else:
                    runtime_info = RuntimeInfo(
                        date=date,
                        custom_secrets_descriptions=obs.custom_secrets_descriptions,
                        working_dir=obs.working_dir,
                    )

                conversation_instructions = None

                if obs.conversation_instructions:
                    conversation_instructions = ConversationInstructions(
                        content=obs.conversation_instructions
                    )

                repo_instructions = (
                    obs.repo_instructions if obs.repo_instructions else ''
                )

                # Have some meaningful content before calling the template
                has_repo_info = repo_info is not None and (
                    repo_info.repo_name or repo_info.repo_directory
                )
                has_runtime_info = runtime_info is not None and (
                    runtime_info.date or runtime_info.custom_secrets_descriptions
                )
                has_repo_instructions = bool(repo_instructions.strip())
                has_conversation_instructions = conversation_instructions is not None

                # Filter and process microagent knowledge
                filtered_agents = []
                if obs.microagent_knowledge:
                    # Exclude disabled microagents
                    filtered_agents = [
                        agent
                        for agent in obs.microagent_knowledge
                        if agent.name not in self.agent_config.disabled_microagents
                    ]

                has_microagent_knowledge = bool(filtered_agents)

                # Generate appropriate content based on what is present
                message_content: list[TextContent | ImageContent] = []

                # Build the workspace context information
                if (
                    has_repo_info
                    or has_runtime_info
                    or has_repo_instructions
                    or has_conversation_instructions
                ):
                    formatted_workspace_text = (
                        self.prompt_manager.build_workspace_context(
                            repository_info=repo_info,
                            runtime_info=runtime_info,
                            conversation_instructions=conversation_instructions,
                            repo_instructions=repo_instructions,
                        )
                    )
                    message_content.append(TextContent(text=formatted_workspace_text))

                # Add microagent knowledge if present
                if has_microagent_knowledge:
                    formatted_microagent_text = (
                        self.prompt_manager.build_microagent_info(
                            triggered_agents=filtered_agents,
                        )
                    )
                    message_content.append(TextContent(text=formatted_microagent_text))

                # Return the combined message if we have any content
                if message_content:
                    message = Message(role='user', content=message_content)
                else:
                    return []
            elif obs.recall_type == RecallType.KNOWLEDGE:
                # Use prompt manager to build the microagent info
                # First, filter out agents that appear in earlier RecallObservations
                filtered_agents = self._filter_agents_in_microagent_obs(
                    obs, current_index, events or []
                )

                # Create and return a message if there is microagent knowledge to include
                if filtered_agents:
                    # Exclude disabled microagents
                    filtered_agents = [
                        agent
                        for agent in filtered_agents
                        if agent.name not in self.agent_config.disabled_microagents
                    ]

                    # Only proceed if we still have agents after filtering out disabled ones
                    if filtered_agents:
                        formatted_text = self.prompt_manager.build_microagent_info(
                            triggered_agents=filtered_agents,
                        )

                        return [
                            Message(
                                role='user', content=[TextContent(text=formatted_text)]
                            )
                        ]

                # Return empty list if no microagents to include or all were disabled
                return []
        elif (
            isinstance(obs, RecallObservation)
            and not self.agent_config.enable_prompt_extensions
        ):
            # If prompt extensions are disabled, we don't add any additional info
            # TODO: test this
            return []
        else:
            # If an observation message is not returned, it will cause an error
            # when the LLM tries to return the next message
            raise ValueError(f'Unknown observation type: {type(obs)}')

        # Update the message as tool response properly
        if (tool_call_metadata := getattr(obs, 'tool_call_metadata', None)) is not None:
            tool_call_id_to_message[tool_call_metadata.tool_call_id] = Message(
                role='tool',
                content=message.content,
                tool_call_id=tool_call_metadata.tool_call_id,
                name=tool_call_metadata.function_name,
            )
            # No need to return the observation message
            # because it will be added by get_action_message when all the corresponding
            # tool calls in the SAME request are processed
            return []

        return [message]