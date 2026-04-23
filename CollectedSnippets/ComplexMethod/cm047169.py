def visit_Tuple(self, node):
        if len(node.elts) != 3 or not isinstance(node.elts[0], ast.Constant):
            return self.generic_visit(node)
        value_node = node.elts[2]
        if isinstance(value_node, (ast.Tuple, ast.List)):
            # convert values one by one
            value_node.elts = [
                self.visit_Tuple(ast.Tuple([ast.Constant('x'), ast.Constant('='), el])).elts[2]
                for el in value_node.elts
            ]
            return node
        value = self.visit(value_node)
        if isinstance(value, str):
            # remove now
            value = value.removeprefix('now ')
            # remove today (if possible)
            if value.startswith('today ') and re.search(r'=\d+[dmy]|=[a-z]', value):
                value = value.removeprefix('today ')
            # update the operator?
            if '!' in value:
                value = value.replace('!', '')
                operator = node.elts[1].value
                if operator == '>':
                    operator += '='
                elif operator == '<=':
                    operator = operator[:-1]
                else:
                    return self._cannot_parse(node)
                node.elts[1].value = operator
            node.elts[2] = ast.Constant(value)
            if not self.log:
                self.log = []
        return node