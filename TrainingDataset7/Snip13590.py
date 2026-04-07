def __init__(self, varname=None, path=None):
        if path is None:
            raise template.TemplateSyntaxError(
                "Static template nodes must be given a path to return."
            )
        self.path = path
        self.varname = varname