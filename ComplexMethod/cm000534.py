async def execute_code(
        self,
        api_key: str,
        code: str,
        language: ProgrammingLanguage,
        template_id: str = "",
        setup_commands: Optional[list[str]] = None,
        timeout: Optional[int] = None,
        sandbox_id: Optional[str] = None,
        dispose_sandbox: bool = False,
        execution_context: Optional["ExecutionContext"] = None,
        extract_files: bool = False,
    ):
        """
        Unified code execution method that handles all three use cases:
        1. Create new sandbox and execute (ExecuteCodeBlock)
        2. Create new sandbox, execute, and return sandbox_id (InstantiateCodeSandboxBlock)
        3. Connect to existing sandbox and execute (ExecuteCodeStepBlock)

        Args:
            extract_files: If True and execution_context provided, extract files
                           created/modified during execution and store to workspace.
        """  # noqa
        sandbox = None
        files: list[SandboxFileOutput] = []
        try:
            if sandbox_id:
                # Connect to existing sandbox (ExecuteCodeStepBlock case)
                sandbox = await AsyncSandbox.connect(
                    sandbox_id=sandbox_id, api_key=api_key
                )
            else:
                # Create new sandbox (ExecuteCodeBlock/InstantiateCodeSandboxBlock case)
                sandbox = await AsyncSandbox.create(
                    api_key=api_key, template=template_id, timeout=timeout
                )
                if setup_commands:
                    for cmd in setup_commands:
                        await sandbox.commands.run(cmd)

            # Capture timestamp before execution to scope file extraction
            start_timestamp = None
            if extract_files:
                ts_result = await sandbox.commands.run("date -u +%Y-%m-%dT%H:%M:%S")
                start_timestamp = ts_result.stdout.strip() if ts_result.stdout else None

            # Execute the code
            execution = await sandbox.run_code(  # type: ignore[attr-defined]
                code,
                language=language.value,
                on_error=lambda e: sandbox.kill(),  # Kill the sandbox on error
            )

            if execution.error:
                raise Exception(execution.error)

            results = execution.results
            text_output = execution.text
            stdout_logs = "".join(execution.logs.stdout)
            stderr_logs = "".join(execution.logs.stderr)

            # Extract files created/modified during this execution
            if extract_files and execution_context:
                files = await extract_and_store_sandbox_files(
                    sandbox=sandbox,
                    working_directory=self.WORKING_DIR,
                    execution_context=execution_context,
                    since_timestamp=start_timestamp,
                    text_only=False,  # Include binary files too
                )

            return (
                results,
                text_output,
                stdout_logs,
                stderr_logs,
                sandbox.sandbox_id,
                files,
            )
        finally:
            # Dispose of sandbox if requested to reduce usage costs
            if dispose_sandbox and sandbox:
                await sandbox.kill()