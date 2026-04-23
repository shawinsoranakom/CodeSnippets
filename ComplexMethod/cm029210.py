def log_response(response: AgentOutput, registry=None, logger=None) -> None:
	"""Utility function to log the model's response."""

	# Use module logger if no logger provided
	if logger is None:
		logger = logging.getLogger(__name__)

	# Only log thinking if it's present
	if response.current_state.thinking:
		logger.debug(f'💡 Thinking:\n{response.current_state.thinking}')

	# Only log evaluation if it's not empty
	eval_goal = response.current_state.evaluation_previous_goal
	if eval_goal:
		if 'success' in eval_goal.lower():
			emoji = '👍'
			# Green color for success
			logger.info(f'  \033[32m{emoji} Eval: {eval_goal}\033[0m')
		elif 'failure' in eval_goal.lower():
			emoji = '⚠️'
			# Red color for failure
			logger.info(f'  \033[31m{emoji} Eval: {eval_goal}\033[0m')
		else:
			emoji = '❔'
			# No color for unknown/neutral
			logger.info(f'  {emoji} Eval: {eval_goal}')

	# Always log memory if present
	if response.current_state.memory:
		logger.info(f'  🧠 Memory: {response.current_state.memory}')

	# Only log next goal if it's not empty
	next_goal = response.current_state.next_goal
	if next_goal:
		# Blue color for next goal
		logger.info(f'  \033[34m🎯 Next goal: {next_goal}\033[0m')