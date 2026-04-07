def __init__(self, source=None):
            self.imports = set()
            if source:
                tree = ast.parse(source)
                self.visit(tree)