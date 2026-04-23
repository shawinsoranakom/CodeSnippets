def construct_eval_env(self, return_type_str: str, imports) -> dict:
        """Constructs an evaluation environment.

        Constructs an evaluation environment with the necessary imports for the return type,
        taking into account module aliases.
        """
        eval_env: dict = {}
        for import_entry in imports:
            if isinstance(import_entry, tuple):  # from module import name
                module, name = import_entry
                if name in return_type_str:
                    exec(f"import {module}", eval_env)
                    exec(f"from {module} import {name}", eval_env)
            else:  # import module
                module = import_entry
                alias = None
                if " as " in module:
                    module, alias = module.split(" as ")
                if module in return_type_str or (alias and alias in return_type_str):
                    exec(f"import {module} as {alias or module}", eval_env)
        return eval_env