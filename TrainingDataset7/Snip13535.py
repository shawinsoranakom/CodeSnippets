def __init__(self, templates=None):
        """
        templates is an optional list of template engine definitions
        (structured like settings.TEMPLATES).
        """
        self._templates = templates
        self._engines = {}