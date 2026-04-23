def has_return(node):
            if isinstance(node, ast.Return):
                return True
            if isinstance(node, ast.If):
                return any(has_return(child) for child in node.body) or any(has_return(child) for child in node.orelse)
            if isinstance(node, ast.Try):
                return (
                    any(has_return(child) for child in node.body)
                    or any(has_return(child) for child in node.handlers)
                    or any(has_return(child) for child in node.finalbody)
                )
            if isinstance(node, ast.For | ast.While):
                return any(has_return(child) for child in node.body) or any(has_return(child) for child in node.orelse)
            if isinstance(node, ast.With):
                return any(has_return(child) for child in node.body)
            return False