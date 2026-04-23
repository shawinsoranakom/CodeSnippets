def _list_serializer(self) -> dict[str, Any]:
        content: list[dict[str, Any]] = []
        role_tool_with_prompt_caching = False
        for item in self.content:
            d = item.model_dump()
            # We have to remove cache_prompt for tool content and move it up to the message level
            # See discussion here for details: https://github.com/BerriAI/litellm/issues/6422#issuecomment-2438765472
            if self.role == 'tool' and item.cache_prompt:
                role_tool_with_prompt_caching = True
                if isinstance(item, TextContent):
                    d.pop('cache_control', None)
                elif isinstance(item, ImageContent):
                    # ImageContent.model_dump() always returns a list
                    # We know d is a list of dicts for ImageContent
                    if hasattr(d, '__iter__'):
                        for d_item in d:
                            if hasattr(d_item, 'pop'):
                                d_item.pop('cache_control', None)

            if isinstance(item, TextContent):
                content.append(d)
            elif isinstance(item, ImageContent) and self.vision_enabled:
                # ImageContent.model_dump() always returns a list
                # We know d is a list for ImageContent
                content.extend([d] if isinstance(d, dict) else d)

        message_dict: dict[str, Any] = {'content': content, 'role': self.role}

        if role_tool_with_prompt_caching:
            message_dict['cache_control'] = {'type': 'ephemeral'}

        # add tool call keys if we have a tool call or response
        return self._add_tool_call_keys(message_dict)