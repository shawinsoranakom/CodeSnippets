def _get_py_docs(self):
        docs = {
            'DOCUMENTATION': {
                'value': None,
                'lineno': 0,
                'end_lineno': 0,
            },
            'EXAMPLES': {
                'value': None,
                'lineno': 0,
                'end_lineno': 0,
            },
            'RETURN': {
                'value': None,
                'lineno': 0,
                'end_lineno': 0,
            },
        }
        for child in self.ast.body:
            if isinstance(child, ast.Assign):
                for grandchild in child.targets:
                    if not isinstance(grandchild, ast.Name):
                        continue

                    if grandchild.id == 'DOCUMENTATION':
                        docs['DOCUMENTATION']['value'] = child.value.value
                        docs['DOCUMENTATION']['lineno'] = child.lineno
                        docs['DOCUMENTATION']['end_lineno'] = (
                            child.lineno + len(child.value.value.splitlines())
                        )
                    elif grandchild.id == 'EXAMPLES':
                        docs['EXAMPLES']['value'] = child.value.value
                        docs['EXAMPLES']['lineno'] = child.lineno
                        docs['EXAMPLES']['end_lineno'] = (
                            child.lineno + len(child.value.value.splitlines())
                        )
                    elif grandchild.id == 'RETURN':
                        docs['RETURN']['value'] = child.value.value
                        docs['RETURN']['lineno'] = child.lineno
                        docs['RETURN']['end_lineno'] = (
                            child.lineno + len(child.value.value.splitlines())
                        )

        return docs