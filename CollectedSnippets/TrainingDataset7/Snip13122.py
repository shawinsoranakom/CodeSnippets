def from_string(self, template_code):
        """
        Create and return a template for the given source code.

        This method is optional.
        """
        raise NotImplementedError(
            "subclasses of BaseEngine should provide a from_string() method"
        )