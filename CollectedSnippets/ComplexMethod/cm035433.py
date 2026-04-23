def maybe_setup_git_hooks(self):
        """Set up git hooks if .openhands/pre-commit.sh exists in the workspace or repository."""
        pre_commit_script = '.openhands/pre-commit.sh'
        read_obs = self.read(FileReadAction(path=pre_commit_script))
        if isinstance(read_obs, ErrorObservation):
            return

        if self.status_callback:
            self.status_callback(
                'info', RuntimeStatus.SETTING_UP_GIT_HOOKS, 'Setting up git hooks...'
            )

        # Ensure the git hooks directory exists
        action = CmdRunAction('mkdir -p .git/hooks')
        obs = self.run_action(action)
        if isinstance(obs, CmdOutputObservation) and obs.exit_code != 0:
            self.log('error', f'Failed to create git hooks directory: {obs.content}')
            return

        # Make the pre-commit script executable
        action = CmdRunAction(f'chmod +x {pre_commit_script}')
        obs = self.run_action(action)
        if isinstance(obs, CmdOutputObservation) and obs.exit_code != 0:
            self.log(
                'error', f'Failed to make pre-commit script executable: {obs.content}'
            )
            return

        # Check if there's an existing pre-commit hook
        pre_commit_hook = '.git/hooks/pre-commit'
        pre_commit_local = '.git/hooks/pre-commit.local'

        # Read the existing pre-commit hook if it exists
        read_obs = self.read(FileReadAction(path=pre_commit_hook))
        if not isinstance(read_obs, ErrorObservation):
            # If the existing hook wasn't created by OpenHands, preserve it
            if 'This hook was installed by OpenHands' not in read_obs.content:
                self.log('info', 'Preserving existing pre-commit hook')
                # Move the existing hook to pre-commit.local
                action = CmdRunAction(f'mv {pre_commit_hook} {pre_commit_local}')
                obs = self.run_action(action)
                if isinstance(obs, CmdOutputObservation) and obs.exit_code != 0:
                    self.log(
                        'error',
                        f'Failed to preserve existing pre-commit hook: {obs.content}',
                    )
                    return

                # Make it executable
                action = CmdRunAction(f'chmod +x {pre_commit_local}')
                obs = self.run_action(action)
                if isinstance(obs, CmdOutputObservation) and obs.exit_code != 0:
                    self.log(
                        'error',
                        f'Failed to make preserved hook executable: {obs.content}',
                    )
                    return

        # Create the pre-commit hook that calls our script
        pre_commit_hook_content = f"""#!/bin/bash
# This hook was installed by OpenHands
# It calls the pre-commit script in the .openhands directory

if [ -x "{pre_commit_script}" ]; then
    source "{pre_commit_script}"
    exit $?
else
    echo "Warning: {pre_commit_script} not found or not executable"
    exit 0
fi
"""

        # Write the pre-commit hook
        write_obs = self.write(
            FileWriteAction(path=pre_commit_hook, content=pre_commit_hook_content)
        )
        if isinstance(write_obs, ErrorObservation):
            self.log('error', f'Failed to write pre-commit hook: {write_obs.content}')
            return

        # Make the pre-commit hook executable
        action = CmdRunAction(f'chmod +x {pre_commit_hook}')
        obs = self.run_action(action)
        if isinstance(obs, CmdOutputObservation) and obs.exit_code != 0:
            self.log(
                'error', f'Failed to make pre-commit hook executable: {obs.content}'
            )
            return

        self.log('info', 'Git pre-commit hook installed successfully')