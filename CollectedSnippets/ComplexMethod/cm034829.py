async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        from .pa_provider import execute_safe_code, SAFE_MODULES, MAX_EXEC_TIMEOUT, MAX_RECURSION_DEPTH

        code = arguments.get("code", "")
        if not code:
            return {"error": "code parameter is required"}

        if self.safe_mode:
            # In safe mode the caller cannot override any security parameters
            allowed = SAFE_MODULES
            timeout = MAX_EXEC_TIMEOUT
            max_depth = MAX_RECURSION_DEPTH
        else:
            extra_names = arguments.get("allowed_extra_modules") or []
            allowed = SAFE_MODULES | frozenset(extra_names)
            # Allow callers to reduce (but not exceed) the defaults
            requested_timeout = arguments.get("timeout")
            if requested_timeout is not None:
                try:
                    timeout = min(float(requested_timeout), MAX_EXEC_TIMEOUT)
                except (TypeError, ValueError):
                    return {"error": "timeout must be a number"}
            else:
                timeout = MAX_EXEC_TIMEOUT
            requested_depth = arguments.get("max_depth")
            if requested_depth is not None:
                try:
                    max_depth = min(int(requested_depth), MAX_RECURSION_DEPTH)
                except (TypeError, ValueError):
                    return {"error": "max_depth must be an integer"}
            else:
                max_depth = MAX_RECURSION_DEPTH

        try:
            exec_result = execute_safe_code(
                code,
                allowed_modules=allowed,
                timeout=timeout,
                max_depth=max_depth,
            )
            return exec_result.to_dict()
        except Exception as exc:
            return {"error": f"Execution error: {exc}"}