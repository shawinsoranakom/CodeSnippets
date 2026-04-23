def serialize(message: BaseMessage) -> MessageParam | SystemMessage:
		"""Serialize a custom message to an Anthropic MessageParam.

		Note: Anthropic doesn't have a 'system' role. System messages should be
		handled separately as the system parameter in the API call, not as a message.
		If a SystemMessage is passed here, it will be converted to a user message.
		"""
		if isinstance(message, UserMessage):
			content = AnthropicMessageSerializer._serialize_content(message.content, use_cache=message.cache)
			return MessageParam(role='user', content=content)

		elif isinstance(message, SystemMessage):
			# Anthropic doesn't have system messages in the messages array
			# System prompts are passed separately. Convert to user message.
			return message

		elif isinstance(message, AssistantMessage):
			# Handle content and tool calls
			blocks: list[TextBlockParam | ToolUseBlockParam] = []

			# Add content blocks if present
			if message.content is not None:
				if isinstance(message.content, str):
					# String content: only cache if it's the only/last block (no tool calls)
					blocks.append(
						TextBlockParam(
							text=message.content,
							type='text',
							cache_control=AnthropicMessageSerializer._serialize_cache_control(
								message.cache and not message.tool_calls
							),
						)
					)
				else:
					# Process content parts (text and refusal)
					for i, part in enumerate(message.content):
						# Only last content block gets cache if there are no tool calls
						is_last_content = (i == len(message.content) - 1) and not message.tool_calls
						if part.type == 'text':
							blocks.append(
								AnthropicMessageSerializer._serialize_content_part_text(
									part, use_cache=message.cache and is_last_content
								)
							)
							# # Note: Anthropic doesn't have a specific refusal block type,
							# # so we convert refusals to text blocks
							# elif part.type == 'refusal':
							# 	blocks.append(TextBlockParam(text=f'[Refusal] {part.refusal}', type='text'))

			# Add tool use blocks if present
			if message.tool_calls:
				tool_blocks = AnthropicMessageSerializer._serialize_tool_calls_to_content(
					message.tool_calls, use_cache=message.cache
				)
				blocks.extend(tool_blocks)

			# If no content or tool calls, add empty text block
			# (Anthropic requires at least one content block)
			if not blocks:
				blocks.append(
					TextBlockParam(
						text='', type='text', cache_control=AnthropicMessageSerializer._serialize_cache_control(message.cache)
					)
				)

			# If caching is enabled or we have multiple blocks, return blocks as-is
			# Otherwise, simplify single text blocks to plain string
			if message.cache or len(blocks) > 1:
				content = blocks
			else:
				# Only simplify when no caching and single block
				single_block = blocks[0]
				if single_block['type'] == 'text' and not single_block.get('cache_control'):
					content = single_block['text']
				else:
					content = blocks

			return MessageParam(
				role='assistant',
				content=content,
			)

		else:
			raise ValueError(f'Unknown message type: {type(message)}')