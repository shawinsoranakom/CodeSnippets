def run_action(self, action: Action) -> Observation:
        """Run an action and return the resulting observation.
        If the action is not runnable in any runtime, a NullObservation is returned.
        If the action is not supported by the current runtime, an ErrorObservation is returned.
        """
        if not action.runnable:
            if isinstance(action, AgentThinkAction):
                return AgentThinkObservation('Your thought has been logged.')
            elif isinstance(action, TaskTrackingAction):
                # Get the session-specific task file path
                conversation_dir = get_conversation_dir(
                    self.sid, self.event_stream.user_id
                )
                task_file_path = f'{conversation_dir}TASKS.md'

                if action.command == 'plan':
                    # Write the serialized task list to the session directory
                    content = '# Task List\n\n'
                    for i, task in enumerate(action.task_list, 1):
                        status_icon = {
                            'todo': '⏳',
                            'in_progress': '🔄',
                            'done': '✅',
                        }.get(task.get('status', 'todo'), '⏳')
                        content += f'{i}. {status_icon} {task.get("title", "")}\n{task.get("notes", "")}\n'

                    try:
                        self.event_stream.file_store.write(task_file_path, content)
                        return TaskTrackingObservation(
                            content=f'Task list has been updated with {len(action.task_list)} items. Stored in session directory: {task_file_path}',
                            command=action.command,
                            task_list=action.task_list,
                        )
                    except Exception as e:
                        return ErrorObservation(
                            f'Failed to write task list to session directory {task_file_path}: {str(e)}'
                        )

                elif action.command == 'view':
                    # Read the TASKS.md file from the session directory
                    try:
                        content = self.event_stream.file_store.read(task_file_path)
                        return TaskTrackingObservation(
                            content=content,
                            command=action.command,
                            task_list=[],  # Empty for view command
                        )
                    except FileNotFoundError:
                        return TaskTrackingObservation(
                            command=action.command,
                            task_list=[],
                            content='No task list found. Use the "plan" command to create one.',
                        )
                    except Exception as e:
                        return TaskTrackingObservation(
                            command=action.command,
                            task_list=[],
                            content=f'Failed to read the task list from session directory {task_file_path}. Error: {str(e)}',
                        )
                else:
                    return TaskTrackingObservation(
                        command=action.command,
                        task_list=[],
                        content=f'Unknown command: {action.command}',
                    )
            return NullObservation('')
        if (
            hasattr(action, 'confirmation_state')
            and action.confirmation_state
            == ActionConfirmationStatus.AWAITING_CONFIRMATION
        ):
            return NullObservation('')
        action_type = action.action  # type: ignore[attr-defined]
        if action_type not in ACTION_TYPE_TO_CLASS:
            return ErrorObservation(f'Action {action_type} does not exist.')
        if not hasattr(self, action_type):
            return ErrorObservation(
                f'Action {action_type} is not supported in the current runtime.'
            )
        if (
            getattr(action, 'confirmation_state', None)
            == ActionConfirmationStatus.REJECTED
        ):
            return UserRejectObservation(
                'Action has been rejected by the user! Waiting for further user input.'
            )
        observation = getattr(self, action_type)(action)
        return observation