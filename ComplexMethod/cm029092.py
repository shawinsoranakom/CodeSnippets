def update_tasks_panel(self) -> None:
		"""Update tasks information panel with details about the tasks and steps hierarchy."""
		tasks_info = self.query_one('#tasks-info', RichLog)
		tasks_info.clear()

		if self.agent:
			# Check if agent has tasks
			task_history = []
			message_history = []

			# Try to extract tasks by looking at message history
			if hasattr(self.agent, '_message_manager') and self.agent._message_manager:
				message_history = self.agent._message_manager.state.history.get_messages()

				# Extract original task(s)
				original_tasks = []
				for msg in message_history:
					if hasattr(msg, 'content'):
						content = msg.content
						if isinstance(content, str) and 'Your ultimate task is:' in content:
							task_text = content.split('"""')[1].strip()
							original_tasks.append(task_text)

				if original_tasks:
					tasks_info.write('[bold green]TASK:[/]')
					for i, task in enumerate(original_tasks, 1):
						# Only show latest task if multiple task changes occurred
						if i == len(original_tasks):
							tasks_info.write(f'[white]{task}[/]')
					tasks_info.write('')

			# Get current state information
			current_step = self.agent.state.n_steps if hasattr(self.agent, 'state') else 0

			# Get all agent history items
			history_items = []
			if hasattr(self.agent, 'state') and hasattr(self.agent.state, 'history'):
				history_items = self.agent.history.history

				if history_items:
					tasks_info.write('[bold yellow]STEPS:[/]')

					for idx, item in enumerate(history_items, 1):
						# Determine step status
						step_style = '[green]✓[/]'

						# For the current step, show it as in progress
						if idx == current_step:
							step_style = '[yellow]⟳[/]'

						# Check if this step had an error
						if item.result and any(result.error for result in item.result):
							step_style = '[red]✗[/]'

						# Show step number
						tasks_info.write(f'{step_style} Step {idx}/{current_step}')

						# Show goal if available
						if item.model_output and hasattr(item.model_output, 'current_state'):
							# Show goal for this step
							goal = item.model_output.current_state.next_goal
							if goal:
								# Take just the first line for display
								goal_lines = goal.strip().split('\n')
								goal_summary = goal_lines[0]
								tasks_info.write(f'   [cyan]Goal:[/] {goal_summary}')

							# Show evaluation of previous goal (feedback)
							eval_prev = item.model_output.current_state.evaluation_previous_goal
							if eval_prev and idx > 1:  # Only show for steps after the first
								eval_lines = eval_prev.strip().split('\n')
								eval_summary = eval_lines[0]
								eval_summary = eval_summary.replace('Success', '✅ ').replace('Failed', '❌ ').strip()
								tasks_info.write(f'   [tan]Evaluation:[/] {eval_summary}')

						# Show actions taken in this step
						if item.model_output and item.model_output.action:
							tasks_info.write('   [purple]Actions:[/]')
							for action_idx, action in enumerate(item.model_output.action, 1):
								action_type = action.__class__.__name__
								if hasattr(action, 'model_dump'):
									# For proper actions, show the action type
									action_dict = action.model_dump(exclude_unset=True)
									if action_dict:
										action_name = list(action_dict.keys())[0]
										tasks_info.write(f'     {action_idx}. [blue]{action_name}[/]')

						# Show results or errors from this step
						if item.result:
							for result in item.result:
								if result.error:
									error_text = result.error
									tasks_info.write(f'   [red]Error:[/] {error_text}')
								elif result.extracted_content:
									content = result.extracted_content
									tasks_info.write(f'   [green]Result:[/] {content}')

						# Add a space between steps for readability
						tasks_info.write('')

			# If agent is actively running, show a status indicator
			if hasattr(self.agent, 'running') and getattr(self.agent, 'running', False):
				tasks_info.write('[yellow]Agent is actively working[blink]...[/][/]')
			elif hasattr(self.agent, 'state') and hasattr(self.agent.state, 'paused') and self.agent.state.paused:
				tasks_info.write('[orange]Agent is paused (press Enter to resume)[/]')
		else:
			tasks_info.write('[dim]Agent not initialized[/]')

		# Force scroll to bottom
		tasks_panel = self.query_one('#tasks-panel')
		tasks_panel.scroll_end(animate=False)