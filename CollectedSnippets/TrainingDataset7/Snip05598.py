def choices(self, changelist):
        """
        Return choices ready to be output in the template.

        `changelist` is the ChangeList to be displayed.
        """
        raise NotImplementedError(
            "subclasses of ListFilter must provide a choices() method"
        )