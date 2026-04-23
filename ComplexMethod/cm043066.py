def compile_hook(self, hook_code: str, hook_point: str) -> Optional[Callable]:
        """
        Compile user-provided hook code into a callable function

        Args:
            hook_code: The Python code string
            hook_point: The hook point name

        Returns:
            Compiled function or None if compilation failed
        """
        try:
            # Create a safe namespace for the hook
            # SECURITY: No __import__ to prevent arbitrary module imports (RCE risk)
            import builtins
            safe_builtins = {}

            # Add safe built-in functions (no __import__ for security)
            allowed_builtins = [
                'print', 'len', 'str', 'int', 'float', 'bool',
                'list', 'dict', 'set', 'tuple', 'range', 'enumerate',
                'zip', 'map', 'filter', 'any', 'all', 'sum', 'min', 'max',
                'sorted', 'reversed', 'abs', 'round', 'isinstance', 'type',
                'getattr', 'hasattr', 'setattr', 'callable', 'iter', 'next',
                '__build_class__'  # Required for class definitions in exec
            ]

            for name in allowed_builtins:
                if hasattr(builtins, name):
                    safe_builtins[name] = getattr(builtins, name)

            namespace = {
                '__name__': f'user_hook_{hook_point}',
                '__builtins__': safe_builtins
            }

            # Add commonly needed imports
            exec("import asyncio", namespace)
            exec("import json", namespace)
            exec("import re", namespace)
            exec("from typing import Dict, List, Optional", namespace)

            # Execute the code to define the function
            exec(hook_code, namespace)

            # Find the async function in the namespace
            for name, obj in namespace.items():
                if callable(obj) and not name.startswith('_') and asyncio.iscoroutinefunction(obj):
                    return obj

            # If no async function found, look for any function
            for name, obj in namespace.items():
                if callable(obj) and not name.startswith('_'):
                    logger.warning(f"Found non-async function '{name}' - wrapping it")
                    # Wrap sync function in async
                    async def async_wrapper(*args, **kwargs):
                        return obj(*args, **kwargs)
                    return async_wrapper

            raise ValueError("No callable function found in hook code")

        except Exception as e:
            error = {
                'hook_point': hook_point,
                'error': f"Failed to compile hook: {str(e)}",
                'type': 'compilation_error',
                'traceback': traceback.format_exc()
            }
            self.errors.append(error)
            logger.error(f"Hook compilation failed for {hook_point}: {str(e)}")
            return None