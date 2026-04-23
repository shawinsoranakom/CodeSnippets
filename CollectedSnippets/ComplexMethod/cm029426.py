async def select_option(self, values: str | list[str]) -> None:
		"""Select option(s) in a select element."""
		if isinstance(values, str):
			values = [values]

		# Focus the element first
		try:
			await self.focus()
		except Exception:
			logger.warning('Failed to focus element')

		# For select elements, we need to find option elements and click them
		# This is a simplified approach - in practice, you might need to handle
		# different select types (single vs multi-select) differently
		node_id = await self._get_node_id()

		# Request child nodes to get the options
		params: 'RequestChildNodesParameters' = {'nodeId': node_id, 'depth': 1}
		await self._client.send.DOM.requestChildNodes(params, session_id=self._session_id)

		# Get the updated node description with children
		describe_params: 'DescribeNodeParameters' = {'nodeId': node_id, 'depth': 1}
		describe_result = await self._client.send.DOM.describeNode(describe_params, session_id=self._session_id)

		select_node = describe_result['node']

		# Find and select matching options
		for child in select_node.get('children', []):
			if child.get('nodeName', '').lower() == 'option':
				# Get option attributes
				attrs = child.get('attributes', [])
				option_attrs = {}
				for i in range(0, len(attrs), 2):
					if i + 1 < len(attrs):
						option_attrs[attrs[i]] = attrs[i + 1]

				option_value = option_attrs.get('value', '')
				option_text = child.get('nodeValue', '')

				# Check if this option should be selected
				should_select = option_value in values or option_text in values

				if should_select:
					# Click the option to select it
					option_node_id = child.get('nodeId')
					if option_node_id:
						# Get backend node ID for the option
						option_describe_params: 'DescribeNodeParameters' = {'nodeId': option_node_id}
						option_backend_result = await self._client.send.DOM.describeNode(
							option_describe_params, session_id=self._session_id
						)
						option_backend_id = option_backend_result['node']['backendNodeId']

						# Create an Element for the option and click it
						option_element = Element(self._browser_session, option_backend_id, self._session_id)
						await option_element.click()