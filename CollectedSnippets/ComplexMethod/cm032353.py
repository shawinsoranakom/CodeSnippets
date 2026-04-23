def _execute_code(self, language: str, code: str, arguments: dict):
        import requests

        if self.check_if_canceled("CodeExec execution"):
            return self.output()

        timeout_seconds = int(os.environ.get("COMPONENT_EXEC_TIMEOUT", 10 * 60))

        try:
            # Try using the new sandbox provider system first
            try:
                from agent.sandbox.client import execute_code as sandbox_execute_code

                if self.check_if_canceled("CodeExec execution"):
                    return

                # Execute code using the provider system
                result = sandbox_execute_code(code=code, language=language, timeout=timeout_seconds, arguments=arguments)

                if self.check_if_canceled("CodeExec execution"):
                    return

                artifacts = result.metadata.get("artifacts", []) if result.metadata else []
                return self._process_execution_result(
                    result.stdout,
                    result.stderr,
                    "Provider system",
                    artifacts,
                    execution_metadata=result.metadata,
                )

            except (ImportError, RuntimeError) as provider_error:
                # Provider system not available or not configured, fall back to HTTP
                logging.info(f"[CodeExec]: Provider system not available, using HTTP fallback: {provider_error}")

            # Fallback to direct HTTP request
            code_b64 = self._encode_code(code)
            code_req = CodeExecutionRequest(code_b64=code_b64, language=language, arguments=arguments).model_dump()
        except Exception as e:
            if self.check_if_canceled("CodeExec execution"):
                return self.output()

            self.set_output("_ERROR", "construct code request error: " + str(e))
            return self.output()

        try:
            if self.check_if_canceled("CodeExec execution"):
                self.set_output("_ERROR", "Task has been canceled")
                return self.output()

            resp = requests.post(url=f"http://{settings.SANDBOX_HOST}:9385/run", json=code_req, timeout=timeout_seconds)
            logging.info(f"http://{settings.SANDBOX_HOST}:9385/run,  code_req: {code_req}, resp.status_code {resp.status_code}:")

            if self.check_if_canceled("CodeExec execution"):
                return "Task has been canceled"

            if resp.status_code != 200:
                resp.raise_for_status()
            body = resp.json()
            if body:
                return self._process_execution_result(
                    body.get("stdout", ""),
                    body.get("stderr"),
                    f"http://{settings.SANDBOX_HOST}:9385/run",
                    body.get("artifacts", []),
                    execution_metadata=self._build_http_execution_metadata(body),
                )
            else:
                self.set_output("_ERROR", "There is no response from sandbox")
                return self.output()

        except Exception as e:
            if self.check_if_canceled("CodeExec execution"):
                return self.output()

            self.set_output("_ERROR", "Exception executing code: " + str(e))

        return self.output()