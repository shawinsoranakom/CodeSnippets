def from_code(cls, code):
        tree = ast.parse(code)
        locator = cls()
        locator.visit(tree)
        return locator