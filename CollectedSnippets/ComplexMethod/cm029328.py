async def on_ScrollToTextEvent(self, event: ScrollToTextEvent) -> None:
		"""Handle scroll to text request with CDP. Raises exception if text not found."""

		# TODO: handle looking for text inside cross-origin iframes as well

		# Get focused CDP session using public API (validates and waits for recovery if needed)
		cdp_session = await self.browser_session.get_or_create_cdp_session()
		cdp_client = cdp_session.cdp_client
		session_id = cdp_session.session_id

		# Enable DOM
		await cdp_client.send.DOM.enable(session_id=session_id)

		# Get document
		doc = await cdp_client.send.DOM.getDocument(params={'depth': -1}, session_id=session_id)
		root_node_id = doc['root']['nodeId']

		# Search for text using XPath
		search_queries = [
			f'//*[contains(text(), "{event.text}")]',
			f'//*[contains(., "{event.text}")]',
			f'//*[@*[contains(., "{event.text}")]]',
		]

		found = False
		for query in search_queries:
			try:
				# Perform search
				search_result = await cdp_client.send.DOM.performSearch(params={'query': query}, session_id=session_id)
				search_id = search_result['searchId']
				result_count = search_result['resultCount']

				if result_count > 0:
					# Get the first match
					node_ids = await cdp_client.send.DOM.getSearchResults(
						params={'searchId': search_id, 'fromIndex': 0, 'toIndex': 1},
						session_id=session_id,
					)

					if node_ids['nodeIds']:
						node_id = node_ids['nodeIds'][0]

						# Scroll the element into view
						await cdp_client.send.DOM.scrollIntoViewIfNeeded(params={'nodeId': node_id}, session_id=session_id)

						found = True
						self.logger.debug(f'📜 Scrolled to text: "{event.text}"')
						break

				# Clean up search
				await cdp_client.send.DOM.discardSearchResults(params={'searchId': search_id}, session_id=session_id)
			except Exception as e:
				self.logger.debug(f'Search query failed: {query}, error: {e}')
				continue

		if not found:
			# Fallback: Try JavaScript search
			js_result = await cdp_client.send.Runtime.evaluate(
				params={
					'expression': f'''
							(() => {{
								const walker = document.createTreeWalker(
									document.body,
									NodeFilter.SHOW_TEXT,
									null,
									false
								);
								let node;
								while (node = walker.nextNode()) {{
									if (node.textContent.includes("{event.text}")) {{
										node.parentElement.scrollIntoView({{behavior: 'smooth', block: 'center'}});
										return true;
									}}
								}}
								return false;
							}})()
						'''
				},
				session_id=session_id,
			)

			if js_result.get('result', {}).get('value'):
				self.logger.debug(f'📜 Scrolled to text: "{event.text}" (via JS)')
				return None
			else:
				self.logger.warning(f'⚠️ Text not found: "{event.text}"')
				raise BrowserError(f'Text not found: "{event.text}"', details={'text': event.text})

		# If we got here and found is True, return None (success)
		if found:
			return None
		else:
			raise BrowserError(f'Text not found: "{event.text}"', details={'text': event.text})