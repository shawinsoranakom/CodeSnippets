def get_prompt_description(self, page_url: str | None = None) -> str:
		"""Get a description of all actions for the prompt

		Args:
			page_url: If provided, filter actions by URL using domain filters.

		Returns:
			A string description of available actions.
			- If page is None: return only actions with no page_filter and no domains (for system prompt)
			- If page is provided: return only filtered actions that match the current page (excluding unfiltered actions)
		"""
		if page_url is None:
			# For system prompt (no URL provided), include only actions with no filters
			return '\n'.join(action.prompt_description() for action in self.actions.values() if action.domains is None)

		# only include filtered actions for the current page URL
		filtered_actions = []
		for action in self.actions.values():
			if not action.domains:
				# skip actions with no filters, they are already included in the system prompt
				continue

			# Check domain filter
			if self._match_domains(action.domains, page_url):
				filtered_actions.append(action)

		return '\n'.join(action.prompt_description() for action in filtered_actions)