def is_mutated(n):
            """Check if a node is mutated by any in-place operation."""
            for user in n.users:
                if user.op != "call_function" or not hasattr(user.target, "_schema"):
                    continue
                for i, arg in enumerate(user.args):
                    if arg is n:
                        schema_arg = user.target._schema.arguments[i]
                        if schema_arg.alias_info and schema_arg.alias_info.is_write:
                            return True
            return False