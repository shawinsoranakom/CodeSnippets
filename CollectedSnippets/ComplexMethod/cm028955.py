async def capture_ainvoke(*args, **kwargs):
			if args:
				for msg in args[0]:
					content = getattr(msg, 'content', '')
					if isinstance(content, str):
						captured_content.append(content)
					elif isinstance(content, list):
						for part in content:
							if isinstance(part, dict) and part.get('type') == 'text':
								captured_content.append(part.get('text', ''))
			return ChatInvokeCompletion(completion='Widget A image: http://localhost/images/widget-a.jpg', usage=None)