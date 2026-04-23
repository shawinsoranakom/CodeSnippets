def get_globals(self, global_imports: str | list[str]) -> dict:
        """Create a globals dictionary with only the specified allowed imports."""
        global_dict = {}

        try:
            if isinstance(global_imports, str):
                modules = [module.strip() for module in global_imports.split(",")]
            elif isinstance(global_imports, list):
                modules = global_imports
            else:
                msg = "global_imports must be either a string or a list"
                raise TypeError(msg)

            for module in modules:
                try:
                    imported_module = importlib.import_module(module)
                    global_dict[imported_module.__name__] = imported_module
                except ImportError as e:
                    msg = f"Could not import module {module}: {e!s}"
                    raise ImportError(msg) from e

        except Exception as e:
            self.log(f"Error in global imports: {e!s}")
            raise
        else:
            self.log(f"Successfully imported modules: {list(global_dict.keys())}")
            return global_dict