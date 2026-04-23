async def _type_text(self, index: int, text: str) -> str:
		"""Type text into an element."""
		if not self.browser_session:
			return 'Error: No browser session active'

		element = await self.browser_session.get_dom_element_by_index(index)
		if not element:
			return f'Element with index {index} not found'

		from browser_use.browser.events import TypeTextEvent

		# Conservative heuristic to detect potentially sensitive data
		# Only flag very obvious patterns to minimize false positives
		is_potentially_sensitive = len(text) >= 6 and (
			# Email pattern: contains @ and a domain-like suffix
			('@' in text and '.' in text.split('@')[-1] if '@' in text else False)
			# Mixed alphanumeric with reasonable complexity (likely API keys/tokens)
			or (
				len(text) >= 16
				and any(char.isdigit() for char in text)
				and any(char.isalpha() for char in text)
				and any(char in '.-_' for char in text)
			)
		)

		# Use generic key names to avoid information leakage about detection patterns
		sensitive_key_name = None
		if is_potentially_sensitive:
			if '@' in text and '.' in text.split('@')[-1]:
				sensitive_key_name = 'email'
			else:
				sensitive_key_name = 'credential'

		event = self.browser_session.event_bus.dispatch(
			TypeTextEvent(node=element, text=text, is_sensitive=is_potentially_sensitive, sensitive_key_name=sensitive_key_name)
		)
		await event

		if is_potentially_sensitive:
			if sensitive_key_name:
				return f'Typed <{sensitive_key_name}> into element {index}'
			else:
				return f'Typed <sensitive> into element {index}'
		else:
			return f"Typed '{text}' into element {index}"