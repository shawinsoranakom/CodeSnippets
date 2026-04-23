def serialize_messages(messages: list[BaseMessage]) -> list[Message]:
		"""
		Serialize a list of browser-use messages to OCI Raw API Message objects.

		Args:
		    messages: List of browser-use messages

		Returns:
		    List of OCI Message objects
		"""
		oci_messages = []

		for message in messages:
			oci_message = Message()

			if isinstance(message, UserMessage):
				oci_message.role = 'USER'
				content = message.content
				if isinstance(content, str):
					text_content = TextContent()
					text_content.text = content
					oci_message.content = [text_content]
				elif isinstance(content, list):
					# Handle content parts - text and images
					contents = []
					for part in content:
						if part.type == 'text':
							text_content = TextContent()
							text_content.text = part.text
							contents.append(text_content)
						elif part.type == 'image_url':
							image_content = OCIRawMessageSerializer._create_image_content(part)
							contents.append(image_content)
					if contents:
						oci_message.content = contents

			elif isinstance(message, SystemMessage):
				oci_message.role = 'SYSTEM'
				content = message.content
				if isinstance(content, str):
					text_content = TextContent()
					text_content.text = content
					oci_message.content = [text_content]
				elif isinstance(content, list):
					# Handle content parts - typically just text for system messages
					contents = []
					for part in content:
						if part.type == 'text':
							text_content = TextContent()
							text_content.text = part.text
							contents.append(text_content)
						elif part.type == 'image_url':
							# System messages can theoretically have images too
							image_content = OCIRawMessageSerializer._create_image_content(part)
							contents.append(image_content)
					if contents:
						oci_message.content = contents

			elif isinstance(message, AssistantMessage):
				oci_message.role = 'ASSISTANT'
				content = message.content
				if isinstance(content, str):
					text_content = TextContent()
					text_content.text = content
					oci_message.content = [text_content]
				elif isinstance(content, list):
					# Handle content parts - text, images, and refusals
					contents = []
					for part in content:
						if part.type == 'text':
							text_content = TextContent()
							text_content.text = part.text
							contents.append(text_content)
						elif part.type == 'image_url':
							# Assistant messages can have images in responses
							# Note: This is currently unreachable in browser-use but kept for completeness
							image_content = OCIRawMessageSerializer._create_image_content(part)
							contents.append(image_content)
						elif part.type == 'refusal':
							text_content = TextContent()
							text_content.text = f'[Refusal] {part.refusal}'
							contents.append(text_content)
					if contents:
						oci_message.content = contents
			else:
				# Fallback for any message format issues
				oci_message.role = 'USER'
				text_content = TextContent()
				text_content.text = str(message)
				oci_message.content = [text_content]

			# Only append messages that have content
			if hasattr(oci_message, 'content') and oci_message.content:
				oci_messages.append(oci_message)

		return oci_messages