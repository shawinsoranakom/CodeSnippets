def visit_call(self, node):
        file_path = Path(self.linter.current_file).as_posix()
        if "/test_" in file_path or "/tests/" in file_path:
            return

        node_name = ""
        if isinstance(node.func, astroid.Name):
            node_name = node.func.name
        elif isinstance(node.func, astroid.Attribute):
            node_name = node.func.attrname
        if node_name in self.errors_requiring_gettext and len(node.args) > 0:
            first_arg = node.args[0]
            if not is_whitelisted_argument(first_arg):
                self.add_message("missing-gettext", node=node, args=(node_name,))
                return

        if isinstance(node.func, astroid.Name):
            # direct function call to _
            node_name = node.func.name
        elif isinstance(node.func, astroid.Attribute):
            # method call to env._
            node_name = node.func.attrname
        else:
            return
        if node_name not in ("_", "_lt"):
            return
        first_arg = node.args[0] if node.args else None
        if not (isinstance(first_arg, astroid.Const) and isinstance(first_arg.value, str)):
            self.add_message("gettext-variable", node=node)
            return
        if len(PLACEHOLDER_REGEXP.findall(first_arg.value)) >= 2:
            self.add_message("gettext-placeholders", node=node)
        if re.search(REPR_REGEXP, first_arg.value):
            self.add_message("gettext-repr", node=node)