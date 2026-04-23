async def _log_action(self, action, action_name: str, action_num: int, total_actions: int) -> None:
		"""Log the action before execution with colored formatting"""
		# Color definitions
		blue = '\033[34m'  # Action name
		magenta = '\033[35m'  # Parameter names
		reset = '\033[0m'

		# Format action number and name
		if total_actions > 1:
			action_header = f'▶️  [{action_num}/{total_actions}] {blue}{action_name}{reset}:'
			plain_header = f'▶️  [{action_num}/{total_actions}] {action_name}:'
		else:
			action_header = f'▶️   {blue}{action_name}{reset}:'
			plain_header = f'▶️  {action_name}:'

		# Get action parameters
		action_data = action.model_dump(exclude_unset=True)
		params = action_data.get(action_name, {})

		# Build parameter parts with colored formatting
		param_parts = []
		plain_param_parts = []

		if params and isinstance(params, dict):
			for param_name, value in params.items():
				# Truncate long values for readability
				if isinstance(value, str) and len(value) > 150:
					display_value = value[:150] + '...'
				elif isinstance(value, list) and len(str(value)) > 200:
					display_value = str(value)[:200] + '...'
				else:
					display_value = value

				param_parts.append(f'{magenta}{param_name}{reset}: {display_value}')
				plain_param_parts.append(f'{param_name}: {display_value}')

		# Join all parts
		if param_parts:
			params_string = ', '.join(param_parts)
			self.logger.info(f'  {action_header} {params_string}')
		else:
			self.logger.info(f'  {action_header}')

		if self._demo_mode_enabled:
			panel_message = plain_header
			if plain_param_parts:
				panel_message = f'{panel_message} {", ".join(plain_param_parts)}'
			await self._demo_mode_log(panel_message.strip(), 'action', {'action': action_name, 'step': self.state.n_steps})