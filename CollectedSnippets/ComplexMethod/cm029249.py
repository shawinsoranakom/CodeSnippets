def _get_agent_state_description(self) -> str:
		if self.step_info:
			step_info_description = f'Step{self.step_info.step_number + 1} maximum:{self.step_info.max_steps}\n'
		else:
			step_info_description = ''

		time_str = datetime.now().strftime('%Y-%m-%d')
		step_info_description += f'Today:{time_str}'

		_todo_contents = self.file_system.get_todo_contents() if self.file_system else ''
		if not len(_todo_contents):
			_todo_contents = '[empty todo.md, fill it when applicable]'

		agent_state = f"""
<user_request>
{self.task}
</user_request>
<file_system>
{self.file_system.describe() if self.file_system else 'No file system available'}
</file_system>
<todo_contents>
{_todo_contents}
</todo_contents>
"""
		if self.plan_description:
			agent_state += f'<plan>\n{self.plan_description}\n</plan>\n'

		if self.sensitive_data:
			agent_state += f'<sensitive_data>{self.sensitive_data}</sensitive_data>\n'

		agent_state += f'<step_info>{step_info_description}</step_info>\n'
		if self.available_file_paths:
			available_file_paths_text = '\n'.join(self.available_file_paths)
			agent_state += f'<available_file_paths>{available_file_paths_text}\nUse with absolute paths</available_file_paths>\n'
		return agent_state