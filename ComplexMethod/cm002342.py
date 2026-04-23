def update_body(self, existing_body, new_statements):
        """
        Helper method to update the body by removing duplicates before adding new statements.
        `existing_body` is the body of the original method, the parent class
        `new_statements` are the additional statements
        """
        deduplicated_new_body = []
        existing_nodes = set()
        for node in new_statements:
            if m.matches(node, m.SimpleStatementLine(body=[m.Assign()])):
                target = self.python_module.code_for_node(node.body[0].targets[0].target)
                self.all_assign_target[target] = node
            if m.matches(node, m.SimpleStatementLine(body=[m.Del()])):
                target = self.python_module.code_for_node(node.body[0].target)
                self.deleted_targets[target] = node

        for stmt in existing_body:
            if m.matches(stmt, m.SimpleStatementLine(body=[m.Assign()])):
                target = self.python_module.code_for_node(stmt.body[0].targets[0].target)
                if target in self.deleted_targets:
                    continue
                if target in self.all_assign_target:
                    stmt = self.all_assign_target[target]
            # Skip the docstring (will be added later on, at the beginning)
            elif m.matches(stmt, DOCSTRING_NODE):
                continue
            comment_less_code = re.sub(r"#.*", "", self.python_module.code_for_node(stmt)).strip()
            comment_less_code = re.sub(r"\ *\n", "\n", comment_less_code).strip()
            deduplicated_new_body.append(stmt)
            existing_nodes.add(comment_less_code)

        for node in new_statements:
            code = self.python_module.code_for_node(node)
            comment_less_code = re.sub(r"#.*", "", code).strip()
            comment_less_code = re.sub(r"\ *\n", "\n", comment_less_code).strip()
            if node not in deduplicated_new_body and comment_less_code not in existing_nodes:
                if not m.matches(node, m.SimpleStatementLine(body=[m.Del()])):
                    deduplicated_new_body.append(node)
                    existing_nodes.add(comment_less_code)

        deduplicated_new_body = self._fix_post_init_location(deduplicated_new_body)

        return deduplicated_new_body