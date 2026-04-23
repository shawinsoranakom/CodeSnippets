def execute_code(
        self,
        instance_id: str,
        code: str,
        language: str,
        timeout: int = 10,
        arguments: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Execute code in the sandbox.

        Args:
            instance_id: ID of the sandbox instance (not used for self-managed)
            code: Source code to execute
            language: Programming language (python, nodejs, javascript)
            timeout: Maximum execution time in seconds
            arguments: Optional arguments dict to pass to main() function

        Returns:
            ExecutionResult containing stdout, stderr, exit_code, and metadata

        Raises:
            RuntimeError: If execution fails
            TimeoutError: If execution exceeds timeout
        """
        if not self._initialized:
            raise RuntimeError("Provider not initialized. Call initialize() first.")

        # Normalize language
        normalized_lang = self._normalize_language(language)

        # Prepare request
        code_b64 = base64.b64encode(code.encode("utf-8")).decode("utf-8")
        payload = {
            "code_b64": code_b64,
            "language": normalized_lang,
            "arguments": arguments or {}
        }

        url = f"{self.endpoint}/run"
        exec_timeout = timeout or self.timeout

        start_time = time.time()

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=exec_timeout,
                headers={"Content-Type": "application/json"}
            )

            execution_time = time.time() - start_time

            if response.status_code != 200:
                raise RuntimeError(
                    f"HTTP {response.status_code}: {response.text}"
                )

            result = response.json()
            structured_result = result.get("result") or {}

            return ExecutionResult(
                stdout=result.get("stdout", ""),
                stderr=result.get("stderr", ""),
                exit_code=result.get("exit_code", 0),
                execution_time=execution_time,
                metadata={
                    "status": result.get("status"),
                    "time_used_ms": result.get("time_used_ms"),
                    "memory_used_kb": result.get("memory_used_kb"),
                    "detail": result.get("detail"),
                    "instance_id": instance_id,
                    "artifacts": result.get("artifacts", []),
                    "result_present": structured_result.get("present", False),
                    "result_value": structured_result.get("value"),
                    "result_type": structured_result.get("type"),
                }
            )

        except requests.Timeout:
            execution_time = time.time() - start_time
            raise TimeoutError(
                f"Execution timed out after {exec_timeout} seconds"
            )

        except requests.RequestException as e:
            raise RuntimeError(f"HTTP request failed: {str(e)}")