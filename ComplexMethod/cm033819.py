def visit_call(self, node: astroid.nodes.Call) -> None:
        """Visit a call node."""
        try:
            for i in node.func.inferred():
                func = None

                if isinstance(i.parent, astroid.nodes.Module):
                    parent_module = i.parent.name
                elif isinstance(i.parent, astroid.nodes.If) and isinstance(i.parent.parent, astroid.nodes.Module):
                    parent_module = i.parent.parent.name
                else:
                    parent_module = None

                if parent_module == 'posix':
                    parent_module = 'os'  # some os.* functions we're looking for show up as posix.* imports

                if parent_module and isinstance(i, (astroid.nodes.FunctionDef, astroid.nodes.ClassDef)):
                    func = f'{parent_module}.{i.name}'

                if not func:
                    continue

                entry = self.unwanted_functions.get(func)

                if entry and entry.applies_to(self.linter.current_file):
                    self.add_message(self.BAD_FUNCTION, args=(entry.alternative, func), node=node)
        except astroid.exceptions.InferenceError:
            pass