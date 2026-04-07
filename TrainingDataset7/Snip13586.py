def __init__(self, varname=None, name=None):
        if name is None:
            raise template.TemplateSyntaxError(
                "Prefix nodes must be given a name to return."
            )
        self.varname = varname
        self.name = name