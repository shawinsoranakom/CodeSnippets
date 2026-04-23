def _construct_initial_message_with_plugin_params(
        self,
        initial_message: SendMessageRequest | None,
        plugins: list[PluginSpec] | None,
    ) -> SendMessageRequest | None:
        """Incorporate plugin parameters into the initial message if specified.

        Plugin parameters are formatted and appended to the initial message so the
        agent has context about the user-provided configuration values.

        Args:
            initial_message: The original initial message, if any
            plugins: List of plugin specifications with optional parameters

        Returns:
            The initial message with plugin parameters incorporated, or the
            original message if no plugin parameters are specified
        """
        from openhands.agent_server.models import TextContent

        if not plugins:
            return initial_message

        # Collect formatted parameters from plugins that have them
        plugins_with_params = [p for p in plugins if p.parameters]
        if not plugins_with_params:
            return initial_message

        # Format parameters, grouped by plugin if multiple
        if len(plugins_with_params) == 1:
            params_text = plugins_with_params[0].format_params_as_text()
            plugin_params_message = (
                f'\n\nPlugin Configuration Parameters:\n{params_text}'
            )
        else:
            # Group by plugin name for clarity
            formatted_plugins = []
            for plugin in plugins_with_params:
                params_text = plugin.format_params_as_text(indent='  ')
                if params_text:
                    formatted_plugins.append(f'{plugin.display_name}:\n{params_text}')

            plugin_params_message = (
                '\n\nPlugin Configuration Parameters:\n' + '\n'.join(formatted_plugins)
            )

        if initial_message is None:
            # Create a new message with just the plugin parameters
            return SendMessageRequest(
                content=[TextContent(text=plugin_params_message.strip())],
                run=True,
            )

        # Append plugin parameters to existing message content
        new_content = list(initial_message.content)
        if new_content and isinstance(new_content[-1], TextContent):
            # Append to the last text content
            last_content = new_content[-1]
            new_content[-1] = TextContent(
                text=last_content.text + plugin_params_message,
                cache_prompt=last_content.cache_prompt,
            )
        else:
            # Add as new text content
            new_content.append(TextContent(text=plugin_params_message.strip()))

        return SendMessageRequest(
            role=initial_message.role,
            content=new_content,
            run=initial_message.run,
        )