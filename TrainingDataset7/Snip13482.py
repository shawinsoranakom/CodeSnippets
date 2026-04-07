def get_template_sources(self, template_name):
        """
        An iterator that yields possible matching template paths for a
        template name.
        """
        raise NotImplementedError(
            "subclasses of Loader must provide a get_template_sources() method"
        )