def run_action(self, action: Action) -> Observation:
        self.run_action_calls.append(action)
        # Return a mock git remote URL for git remote get-url commands
        # Use an OLD token to simulate token refresh scenario
        if (
            isinstance(action, CmdRunAction)
            and 'git remote get-url origin' in action.command
        ):
            # Extract provider from previous clone command
            if len(self.run_action_calls) > 0:
                clone_cmd = (
                    self.run_action_calls[0].command if self.run_action_calls else ''
                )
                if 'github.com' in clone_cmd:
                    mock_url = 'https://old_github_token@github.com/owner/repo.git'
                elif 'gitlab.com' in clone_cmd:
                    mock_url = (
                        'https://oauth2:old_gitlab_token@gitlab.com/owner/repo.git'
                    )
                else:
                    mock_url = 'https://github.com/owner/repo.git'
                return CmdOutputObservation(
                    content=mock_url, command_id=-1, command='', exit_code=0
                )
        # Return success for git remote set-url commands
        if (
            isinstance(action, CmdRunAction)
            and 'git remote set-url origin' in action.command
        ):
            return CmdOutputObservation(
                content='', command_id=-1, command='', exit_code=0
            )
        return NullObservation(content='')