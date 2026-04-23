async def execute_claude_code(
        self,
        e2b_api_key: str,
        anthropic_api_key: str,
        prompt: str,
        timeout: int,
        setup_commands: list[str],
        working_directory: str,
        session_id: str,
        existing_sandbox_id: str,
        conversation_history: str,
        dispose_sandbox: bool,
        execution_context: "ExecutionContext",
    ) -> tuple[str, list[SandboxFileOutput], str, str, str]:
        """
        Execute Claude Code in an E2B sandbox.

        Returns:
            Tuple of (response, files, conversation_history, session_id, sandbox_id)
        """

        # Validate that sandbox_id is provided when resuming a session
        if session_id and not existing_sandbox_id:
            raise ValueError(
                "sandbox_id is required when resuming a session with session_id. "
                "The session state is stored in the original sandbox. "
                "If the sandbox has timed out, use conversation_history instead "
                "to restore context on a fresh sandbox."
            )

        sandbox = None
        sandbox_id = ""

        try:
            # Either reconnect to existing sandbox or create a new one
            if existing_sandbox_id:
                # Reconnect to existing sandbox for conversation continuation
                sandbox = await BaseAsyncSandbox.connect(
                    sandbox_id=existing_sandbox_id,
                    api_key=e2b_api_key,
                )
            else:
                # Create new sandbox
                sandbox = await BaseAsyncSandbox.create(
                    template=self.DEFAULT_TEMPLATE,
                    api_key=e2b_api_key,
                    timeout=timeout,
                    envs={"ANTHROPIC_API_KEY": anthropic_api_key},
                )

                # Install Claude Code from npm (ensures we get the latest version)
                install_result = await sandbox.commands.run(
                    "npm install -g @anthropic-ai/claude-code@latest",
                    timeout=120,  # 2 min timeout for install
                )
                if install_result.exit_code != 0:
                    raise Exception(
                        f"Failed to install Claude Code: {install_result.stderr}"
                    )

                # Run any user-provided setup commands
                for cmd in setup_commands:
                    setup_result = await sandbox.commands.run(cmd)
                    if setup_result.exit_code != 0:
                        raise Exception(
                            f"Setup command failed: {cmd}\n"
                            f"Exit code: {setup_result.exit_code}\n"
                            f"Stdout: {setup_result.stdout}\n"
                            f"Stderr: {setup_result.stderr}"
                        )

            # Capture sandbox_id immediately after creation/connection
            # so it's available for error recovery if dispose_sandbox=False
            sandbox_id = sandbox.sandbox_id

            # Generate or use provided session ID
            current_session_id = session_id if session_id else str(uuid.uuid4())

            # Build base Claude flags
            base_flags = "-p --dangerously-skip-permissions --output-format json"

            # Add conversation history context if provided (for fresh sandbox continuation)
            history_flag = ""
            if conversation_history and not session_id:
                # Inject previous conversation as context via system prompt
                # Use consistent escaping via _escape_prompt helper
                escaped_history = self._escape_prompt(
                    f"Previous conversation context: {conversation_history}"
                )
                history_flag = f" --append-system-prompt {escaped_history}"

            # Build Claude command based on whether we're resuming or starting new
            # Use shlex.quote for working_directory and session IDs to prevent injection
            safe_working_dir = shlex.quote(working_directory)
            if session_id:
                # Resuming existing session (sandbox still alive)
                safe_session_id = shlex.quote(session_id)
                claude_command = (
                    f"cd {safe_working_dir} && "
                    f"echo {self._escape_prompt(prompt)} | "
                    f"claude --resume {safe_session_id} {base_flags}"
                )
            else:
                # New session with specific ID
                safe_current_session_id = shlex.quote(current_session_id)
                claude_command = (
                    f"cd {safe_working_dir} && "
                    f"echo {self._escape_prompt(prompt)} | "
                    f"claude --session-id {safe_current_session_id} {base_flags}{history_flag}"
                )

            # Capture timestamp before running Claude Code to filter files later
            # Capture timestamp 1 second in the past to avoid race condition with file creation
            timestamp_result = await sandbox.commands.run(
                "date -u -d '1 second ago' +%Y-%m-%dT%H:%M:%S"
            )
            if timestamp_result.exit_code != 0:
                raise RuntimeError(
                    f"Failed to capture timestamp: {timestamp_result.stderr}"
                )
            start_timestamp = (
                timestamp_result.stdout.strip() if timestamp_result.stdout else None
            )

            result = await sandbox.commands.run(
                claude_command,
                timeout=0,  # No command timeout - let sandbox timeout handle it
            )

            # Check for command failure
            if result.exit_code != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                raise Exception(
                    f"Claude Code command failed with exit code {result.exit_code}:\n"
                    f"{error_msg}"
                )

            raw_output = result.stdout or ""

            # Parse JSON output to extract response and build conversation history
            response = ""
            new_conversation_history = conversation_history or ""

            try:
                # The JSON output contains the result
                output_data = json.loads(raw_output)
                response = output_data.get("result", raw_output)

                # Build conversation history entry
                turn_entry = f"User: {prompt}\nClaude: {response}"
                if new_conversation_history:
                    new_conversation_history = (
                        f"{new_conversation_history}\n\n{turn_entry}"
                    )
                else:
                    new_conversation_history = turn_entry

            except json.JSONDecodeError:
                # If not valid JSON, use raw output
                response = raw_output
                turn_entry = f"User: {prompt}\nClaude: {response}"
                if new_conversation_history:
                    new_conversation_history = (
                        f"{new_conversation_history}\n\n{turn_entry}"
                    )
                else:
                    new_conversation_history = turn_entry

            # Extract files created/modified during this run and store to workspace
            sandbox_files = await extract_and_store_sandbox_files(
                sandbox=sandbox,
                working_directory=working_directory,
                execution_context=execution_context,
                since_timestamp=start_timestamp,
                text_only=True,
            )

            return (
                response,
                sandbox_files,  # Already SandboxFileOutput objects
                new_conversation_history,
                current_session_id,
                sandbox_id,
            )

        except Exception as e:
            # Wrap exception with sandbox_id so caller can access/cleanup
            # the preserved sandbox when dispose_sandbox=False
            raise ClaudeCodeExecutionError(str(e), sandbox_id) from e

        finally:
            if dispose_sandbox and sandbox:
                await sandbox.kill()