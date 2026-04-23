def visit_Rule(self, node: Rule) -> None:
        is_loop = node.is_loop()
        is_gather = node.is_gather()
        rhs = node.flatten()
        if is_loop or is_gather:
            result_type = "asdl_seq *"
        elif node.type:
            result_type = node.type
        else:
            result_type = "void *"

        for line in str(node).splitlines():
            self.print(f"// {line}")
        if node.left_recursive and node.leader:
            self.print(f"static {result_type} {node.name}_raw(Parser *);")

        self.print(f"static {result_type}")
        self.print(f"{node.name}_rule(Parser *p)")

        if node.left_recursive and node.leader:
            self._set_up_rule_memoization(node, result_type)

        self.print("{")

        if node.name.endswith("without_invalid"):
            with self.indent():
                self.print("int _prev_call_invalid = p->call_invalid_rules;")
                self.print("p->call_invalid_rules = 0;")
                self.cleanup_statements.append("p->call_invalid_rules = _prev_call_invalid;")

        if is_loop:
            self._handle_loop_rule_body(node, rhs)
        else:
            self._handle_default_rule_body(node, rhs, result_type)

        if node.name.endswith("without_invalid"):
            self.cleanup_statements.pop()

        self.print("}")