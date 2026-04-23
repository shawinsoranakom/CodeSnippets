def _process_action(
        self,
        action: Action,
        pending_tool_call_action_messages: dict[str, Message],
        vision_is_active: bool = False,
    ) -> list[Message]:
        """Converts an action into a message format that can be sent to the LLM.

        This method handles different types of actions and formats them appropriately:
        1. For tool-based actions (AgentDelegate, CmdRun, IPythonRunCell, FileEdit) and agent-sourced AgentFinish:
            - In function calling mode: Stores the LLM's response in pending_tool_call_action_messages
            - In non-function calling mode: Creates a message with the action string
        2. For MessageActions: Creates a message with the text content and optional image content

        Args:
            action: The action to convert. Can be one of:
                - CmdRunAction: For executing bash commands
                - IPythonRunCellAction: For running IPython code
                - FileEditAction: For editing files
                - FileReadAction: For reading files using openhands-aci commands
                - BrowseInteractiveAction: For browsing the web
                - AgentFinishAction: For ending the interaction
                - MessageAction: For sending messages
                - MCPAction: For interacting with the MCP server
            pending_tool_call_action_messages: Dictionary mapping response IDs to their corresponding messages.
                Used in function calling mode to track tool calls that are waiting for their results.

            vision_is_active: Whether vision is active in the LLM. If True, image URLs will be included

        Returns:
            list[Message]: A list containing the formatted message(s) for the action.
                May be empty if the action is handled as a tool call in function calling mode.

        Note:
            In function calling mode, tool-based actions are stored in pending_tool_call_action_messages
            rather than being returned immediately. They will be processed later when all corresponding
            tool call results are available.
        """
        # create a regular message from an event
        if isinstance(
            action,
            (
                AgentDelegateAction,
                AgentThinkAction,
                IPythonRunCellAction,
                FileEditAction,
                FileReadAction,
                BrowseInteractiveAction,
                BrowseURLAction,
                MCPAction,
                TaskTrackingAction,
            ),
        ) or (isinstance(action, CmdRunAction) and action.source == 'agent'):
            tool_metadata = action.tool_call_metadata

            # Allow user actions to skip tool metadata validation
            if action.source == 'user' and tool_metadata is None:
                # For user-initiated actions without tool metadata, create a simple message
                return [
                    Message(
                        role='user',
                        content=[
                            TextContent(
                                text=f'User requested to read file: {str(action)}'
                            )
                        ],
                    )
                ]

            assert tool_metadata is not None, (
                'Tool call metadata should NOT be None when function calling is enabled for agent actions. Action: '
                + str(action)
            )

            llm_response: ModelResponse = tool_metadata.model_response
            assistant_msg = getattr(llm_response.choices[0], 'message')

            # Add the LLM message (assistant) that initiated the tool calls
            # (overwrites any previous message with the same response_id)
            pending_tool_call_action_messages[llm_response.id] = Message(
                role=getattr(assistant_msg, 'role', 'assistant'),
                # tool call content SHOULD BE a string
                content=[TextContent(text=assistant_msg.content)]
                if assistant_msg.content and assistant_msg.content.strip()
                else [],
                tool_calls=assistant_msg.tool_calls,
            )
            return []
        elif isinstance(action, AgentFinishAction):
            role = 'user' if action.source == 'user' else 'assistant'

            # when agent finishes, it has tool_metadata
            # which has already been executed, and it doesn't have a response
            # when the user finishes (/exit), we don't have tool_metadata
            tool_metadata = action.tool_call_metadata
            if tool_metadata is not None:
                # take the response message from the tool call
                assistant_msg = getattr(
                    tool_metadata.model_response.choices[0], 'message'
                )
                content = assistant_msg.content or ''

                # save content if any, to thought
                if action.thought:
                    if action.thought != content:
                        action.thought += '\n' + content
                else:
                    action.thought = content

                # remove the tool call metadata
                action.tool_call_metadata = None
            if role not in ('user', 'system', 'assistant', 'tool'):
                raise ValueError(f'Invalid role: {role}')
            return [
                Message(
                    role=role,  # type: ignore[arg-type]
                    content=[TextContent(text=action.thought)],
                )
            ]
        elif isinstance(action, MessageAction):
            role = 'user' if action.source == 'user' else 'assistant'
            content = [TextContent(text=action.content or '')]
            if action.image_urls:
                if role == 'user':
                    for idx, url in enumerate(action.image_urls):
                        # Only add descriptive text if vision is active
                        if vision_is_active:
                            content.append(TextContent(text=f'Image {idx + 1}:'))
                        content.append(ImageContent(image_urls=[url]))
                else:
                    content.append(ImageContent(image_urls=action.image_urls))
            if role not in ('user', 'system', 'assistant', 'tool'):
                raise ValueError(f'Invalid role: {role}')
            return [
                Message(
                    role=role,  # type: ignore[arg-type]
                    content=content,
                )
            ]
        elif isinstance(action, CmdRunAction) and action.source == 'user':
            content = [
                TextContent(text=f'User executed the command:\n{action.command}')
            ]
            return [
                Message(
                    role='user',  # Always user for CmdRunAction
                    content=content,
                )
            ]
        elif isinstance(action, SystemMessageAction):
            # Convert SystemMessageAction to a system message
            return [
                Message(
                    role='system',
                    content=[TextContent(text=action.content)],
                    # Include tools if function calling is enabled
                    tool_calls=None,
                )
            ]
        return []