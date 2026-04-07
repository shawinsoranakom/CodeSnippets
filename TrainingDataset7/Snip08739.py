def handle_label(self, label, **options):
        """
        Perform the command's actions for ``label``, which will be the
        string as given on the command line.
        """
        raise NotImplementedError(
            "subclasses of LabelCommand must provide a handle_label() method"
        )