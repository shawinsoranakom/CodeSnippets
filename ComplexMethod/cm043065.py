def validate_hook_structure(self, hook_code: str, hook_point: str) -> Tuple[bool, str]:
        """
        Validate the structure of user-provided hook code

        Args:
            hook_code: The Python code string containing the hook function
            hook_point: The hook point name (e.g., 'on_page_context_created')

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Parse the code
            tree = ast.parse(hook_code)

            # Check if it's empty
            if not tree.body:
                return False, "Hook code is empty"

            # Find the function definition
            func_def = None
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_def = node
                    break

            if not func_def:
                return False, "Hook must contain a function definition (def or async def)"

            # Check if it's async (all hooks should be async)
            if not isinstance(func_def, ast.AsyncFunctionDef):
                return False, f"Hook function must be async (use 'async def' instead of 'def')"

            # Get function name for better error messages
            func_name = func_def.name

            # Validate parameters
            expected_params = self.HOOK_SIGNATURES.get(hook_point, [])
            if not expected_params:
                return False, f"Unknown hook point: {hook_point}"

            func_params = [arg.arg for arg in func_def.args.args]

            # Check if it has **kwargs for flexibility
            has_kwargs = func_def.args.kwarg is not None

            # Must have at least the expected parameters
            missing_params = []
            for expected in expected_params:
                if expected not in func_params:
                    missing_params.append(expected)

            if missing_params and not has_kwargs:
                return False, f"Hook function '{func_name}' must accept parameters: {', '.join(expected_params)} (missing: {', '.join(missing_params)})"

            # Check if it returns something (should return page or browser)
            has_return = any(isinstance(node, ast.Return) for node in ast.walk(func_def))
            if not has_return:
                # Warning, not error - we'll handle this
                logger.warning(f"Hook function '{func_name}' should return the {expected_params[0]} object")

            return True, "Valid"

        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {str(e)}"
        except Exception as e:
            return False, f"Failed to parse hook code: {str(e)}"