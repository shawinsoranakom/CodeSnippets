def process_class_node(self, node, class_details) -> None:
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                if attr := self.parse_assign(stmt):
                    class_details.attributes.append(attr)
            elif isinstance(stmt, ast.AnnAssign):
                if attr := self.parse_ann_assign(stmt):
                    class_details.attributes.append(attr)
            elif isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef):
                method, is_init = self.parse_function_def(stmt)
                if is_init:
                    class_details.init = method
                else:
                    class_details.methods.append(method)