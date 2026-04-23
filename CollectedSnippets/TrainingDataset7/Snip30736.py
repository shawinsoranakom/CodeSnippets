def test_no_fields_cloning(self):
        """
        Cloning a queryset does not get out of hand. While complete
        testing is impossible, this is a sanity check against invalid use of
        deepcopy. refs #16759.
        """
        opts_class = type(Note._meta.get_field("misc"))
        note_deepcopy = getattr(opts_class, "__deepcopy__", None)
        opts_class.__deepcopy__ = lambda obj, memo: self.fail(
            "Model fields shouldn't be cloned"
        )
        try:
            Note.objects.filter(note=F("misc")).all()
        finally:
            if note_deepcopy is None:
                delattr(opts_class, "__deepcopy__")
            else:
                opts_class.__deepcopy__ = note_deepcopy