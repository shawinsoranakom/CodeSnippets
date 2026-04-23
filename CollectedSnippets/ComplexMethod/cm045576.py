async def _execute_command(
        self,
        command: str,
        folder: Optional[str] = None,
        session_name: Optional[str] = None,
        blocking: bool = False,
        timeout: int = 60,
    ) -> ToolResult:
        try:
            # Ensure sandbox is initialized
            await self._ensure_sandbox()

            # Set up working directory
            cwd = self.workspace_path
            if folder:
                folder = folder.strip("/")
                cwd = f"{self.workspace_path}/{folder}"

            # Generate a session name if not provided
            if not session_name:
                session_name = f"session_{str(uuid4())[:8]}"

            # Check if tmux session already exists
            check_session = await self._execute_raw_command(
                f"tmux has-session -t {session_name} 2>/dev/null || echo 'not_exists'"
            )
            session_exists = "not_exists" not in check_session.get("output", "")

            if not session_exists:
                # Create a new tmux session
                await self._execute_raw_command(
                    f"tmux new-session -d -s {session_name}"
                )

            # Ensure we're in the correct directory and send command to tmux
            full_command = f"cd {cwd} && {command}"
            wrapped_command = full_command.replace('"', '\\"')  # Escape double quotes

            # Send command to tmux session
            await self._execute_raw_command(
                f'tmux send-keys -t {session_name} "{wrapped_command}" Enter'
            )

            if blocking:
                # For blocking execution, wait and capture output
                start_time = time.time()
                while (time.time() - start_time) < timeout:
                    # Wait a bit before checking
                    time.sleep(2)

                    # Check if session still exists (command might have exited)
                    check_result = await self._execute_raw_command(
                        f"tmux has-session -t {session_name} 2>/dev/null || echo 'ended'"
                    )
                    if "ended" in check_result.get("output", ""):
                        break

                    # Get current output and check for common completion indicators
                    output_result = await self._execute_raw_command(
                        f"tmux capture-pane -t {session_name} -p -S - -E -"
                    )
                    current_output = output_result.get("output", "")

                    # Check for prompt indicators that suggest command completion
                    last_lines = current_output.split("\n")[-3:]
                    completion_indicators = [
                        "$",
                        "#",
                        ">",
                        "Done",
                        "Completed",
                        "Finished",
                        "✓",
                    ]
                    if any(
                        indicator in line
                        for indicator in completion_indicators
                        for line in last_lines
                    ):
                        break

                # Capture final output
                output_result = await self._execute_raw_command(
                    f"tmux capture-pane -t {session_name} -p -S - -E -"
                )
                final_output = output_result.get("output", "")

                # Kill the session after capture
                await self._execute_raw_command(f"tmux kill-session -t {session_name}")

                return self.success_response(
                    {
                        "output": final_output,
                        "session_name": session_name,
                        "cwd": cwd,
                        "completed": True,
                    }
                )
            else:
                # For non-blocking, just return immediately
                return self.success_response(
                    {
                        "session_name": session_name,
                        "cwd": cwd,
                        "message": f"Command sent to tmux session '{session_name}'. Use check_command_output to view results.",
                        "completed": False,
                    }
                )

        except Exception as e:
            # Attempt to clean up session in case of error
            if session_name:
                try:
                    await self._execute_raw_command(
                        f"tmux kill-session -t {session_name}"
                    )
                except:
                    pass
            return self.fail_response(f"Error executing command: {str(e)}")