async def _get_model_output_with_retry(self, input_messages: list[BaseMessage]) -> AgentOutput:
		"""Get model output with retry logic for empty actions"""
		model_output = await self.get_model_output(input_messages)
		self.logger.debug(
			f'✅ Step {self.state.n_steps}: Got LLM response with {len(model_output.action) if model_output.action else 0} actions'
		)

		if (
			not model_output.action
			or not isinstance(model_output.action, list)
			or all(action.model_dump() == {} for action in model_output.action)
		):
			self.logger.warning('Model returned empty action. Retrying...')

			clarification_message = UserMessage(
				content='You forgot to return an action. Please respond with a valid JSON action according to the expected schema with your assessment and next actions.'
			)

			retry_messages = input_messages + [clarification_message]
			model_output = await self.get_model_output(retry_messages)

			if not model_output.action or all(action.model_dump() == {} for action in model_output.action):
				self.logger.warning('Model still returned empty after retry. Inserting safe noop action.')
				action_instance = self.ActionModel()
				setattr(
					action_instance,
					'done',
					{
						'success': False,
						'text': 'No next action returned by LLM!',
					},
				)
				model_output.action = [action_instance]

		return model_output