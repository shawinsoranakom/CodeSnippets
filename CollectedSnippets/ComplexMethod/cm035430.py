def add_env_vars(self, env_vars: dict[str, str]) -> None:
        env_vars = {key.upper(): value for key, value in env_vars.items()}

        # Add env vars to the IPython shell (if Jupyter is used)
        if any(isinstance(plugin, JupyterRequirement) for plugin in self.plugins):
            code = 'import os\n'
            for key, value in env_vars.items():
                # Note: json.dumps gives us nice escaping for free
                code += f'os.environ["{key}"] = {json.dumps(value)}\n'
            code += '\n'
            self.run_ipython(IPythonRunCellAction(code))
            # Note: we don't log the vars values, they're leaking info
            logger.debug('Added env vars to IPython')

        # Check if we're on Windows
        import os
        import sys

        is_windows = os.name == 'nt' or sys.platform == 'win32'

        if is_windows:
            # Add env vars using PowerShell commands for Windows
            cmd = ''
            for key, value in env_vars.items():
                # Use PowerShell's $env: syntax for environment variables
                # Note: json.dumps gives us nice escaping for free
                cmd += f'$env:{key} = {json.dumps(value)}; '

            if not cmd:
                return

            cmd = cmd.strip()
            logger.debug('Adding env vars to PowerShell')  # don't log the values

            self._run_cmd_with_retry(
                cmd, f'Failed to add env vars [{env_vars.keys()}] to environment'
            )

            # We don't add to profile persistence on Windows as it's more complex
            # and varies between PowerShell versions
            logger.debug(f'Added env vars to PowerShell session: {env_vars.keys()}')

        else:
            # Original bash implementation for Unix systems
            cmd = ''
            bashrc_cmd = ''
            for key, value in env_vars.items():
                # Note: json.dumps gives us nice escaping for free
                cmd += f'export {key}={json.dumps(value)}; '
                # Add to .bashrc if not already present
                bashrc_cmd += f'touch ~/.bashrc; grep -q "^export {key}=" ~/.bashrc || echo "export {key}={json.dumps(value)}" >> ~/.bashrc; '

            if not cmd:
                return

            cmd = cmd.strip()
            logger.debug('Adding env vars to bash')  # don't log the values

            self._run_cmd_with_retry(
                cmd, f'Failed to add env vars [{env_vars.keys()}] to environment'
            )

            # Add to .bashrc for persistence
            bashrc_cmd = bashrc_cmd.strip()
            logger.debug(f'Adding env var to .bashrc: {env_vars.keys()}')
            self._run_cmd_with_retry(
                bashrc_cmd, f'Failed to add env vars [{env_vars.keys()}] to .bashrc'
            )