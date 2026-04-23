async def custom_ainvoke(*args, **kwargs):
		from browser_use.llm.views import ChatInvokeCompletion

		# Verify that we received a message with image content
		messages = args[0] if args else []
		assert len(messages) >= 1, 'Should have at least one message'

		# Check if any message has image content
		has_image = False
		for msg in messages:
			if hasattr(msg, 'content') and isinstance(msg.content, list):
				for part in msg.content:
					if hasattr(part, 'type') and part.type == 'image_url':
						has_image = True
						break

		assert has_image, 'Should include screenshot in message'
		return ChatInvokeCompletion(completion='Extracted content with screenshot analysis', usage=None)