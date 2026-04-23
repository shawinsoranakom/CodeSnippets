def execute_code(self, instance_id: str, code: str, language: str, timeout: int = 10, arguments: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        """
        Execute code in the Aliyun Code Interpreter instance.

        Args:
            instance_id: ID of the sandbox instance
            code: Source code to execute
            language: Programming language (python, javascript)
            timeout: Maximum execution time in seconds (max 30)
            arguments: Optional arguments dict to pass to main() function

        Returns:
            ExecutionResult containing stdout, stderr, exit_code, and metadata

        Raises:
            RuntimeError: If execution fails
            TimeoutError: If execution exceeds timeout
        """
        if not self._initialized or not self._config:
            raise RuntimeError("Provider not initialized. Call initialize() first.")

        # Normalize language
        normalized_lang = self._normalize_language(language)

        # Enforce 30-second hard limit
        timeout = min(timeout or self.timeout, 30)

        try:
            # Connect to existing sandbox instance
            sandbox = Sandbox.connect(sandbox_id=instance_id, config=self._config)

            # agentrun-sdk 0.0.26 only exposes CodeLanguage.PYTHON; keep JS as string fallback.
            code_language = CodeLanguage.PYTHON if normalized_lang == "python" else "javascript"

            # Wrap code to call main() function
            # Matches self_managed provider behavior: call main(**arguments)
            args_json = json.dumps(arguments or {})
            wrapped_code = (
                self._build_python_wrapper(code, args_json)
                if normalized_lang == "python"
                else self._build_javascript_wrapper(code, args_json)
            )
            logger.debug(f"Aliyun Code Interpreter: Wrapped code (first 200 chars): {wrapped_code[:200]}")

            start_time = time.time()

            # Execute code using SDK's simplified execute endpoint
            logger.info(f"Aliyun Code Interpreter: Executing code (language={normalized_lang}, timeout={timeout})")
            logger.debug(f"Aliyun Code Interpreter: Original code (first 200 chars): {code[:200]}")
            result = sandbox.context.execute(
                code=wrapped_code,
                language=code_language,
                timeout=timeout,
            )

            execution_time = time.time() - start_time
            logger.info(f"Aliyun Code Interpreter: Execution completed in {execution_time:.2f}s")
            logger.debug(f"Aliyun Code Interpreter: Raw SDK result: {result}")

            # Parse execution result
            results = result.get("results", []) if isinstance(result, dict) else []
            logger.info(f"Aliyun Code Interpreter: Parsed {len(results)} result items")

            # Extract stdout and stderr from results
            stdout_parts = []
            stderr_parts = []
            exit_code = 0
            execution_status = "ok"

            for item in results:
                result_type = item.get("type", "")
                text = item.get("text", "")

                if result_type == "stdout":
                    stdout_parts.append(text)
                elif result_type == "stderr":
                    stderr_parts.append(text)
                    exit_code = 1  # Error occurred
                elif result_type == "endOfExecution":
                    execution_status = item.get("status", "ok")
                    if execution_status != "ok":
                        exit_code = 1
                elif result_type == "error":
                    stderr_parts.append(text)
                    exit_code = 1

            stdout = "\n".join(stdout_parts)
            stderr = "\n".join(stderr_parts)
            stdout, structured_result = self._extract_structured_result(stdout)

            logger.info(f"Aliyun Code Interpreter: stdout length={len(stdout)}, stderr length={len(stderr)}, exit_code={exit_code}")
            if stdout:
                logger.debug(f"Aliyun Code Interpreter: stdout (first 200 chars): {stdout[:200]}")
            if stderr:
                logger.debug(f"Aliyun Code Interpreter: stderr (first 200 chars): {stderr[:200]}")

            return ExecutionResult(
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                execution_time=execution_time,
                metadata={
                    "instance_id": instance_id,
                    "language": normalized_lang,
                    "context_id": result.get("contextId") if isinstance(result, dict) else None,
                    "timeout": timeout,
                    "result_present": structured_result.get("present", False),
                    "result_value": structured_result.get("value"),
                    "result_type": structured_result.get("type"),
                },
            )

        except ServerError as e:
            if "timeout" in str(e).lower():
                raise TimeoutError(f"Execution timed out after {timeout} seconds")
            raise RuntimeError(f"Failed to execute code: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during execution: {str(e)}")