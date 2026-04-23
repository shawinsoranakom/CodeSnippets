def test_normal_pk(self):
        """
        Normal primary keys work on a model with natural key capabilities.
        """
        management.call_command(
            "loaddata",
            "non_natural_1.json",
            verbosity=0,
        )
        management.call_command(
            "loaddata",
            "forward_ref_lookup.json",
            verbosity=0,
        )
        management.call_command(
            "loaddata",
            "non_natural_2.xml",
            verbosity=0,
        )
        books = Book.objects.all()
        self.assertQuerySetEqual(
            books,
            [
                "<Book: Cryptonomicon by Neal Stephenson (available at Amazon, "
                "Borders)>",
                "<Book: Ender's Game by Orson Scott Card (available at Collins "
                "Bookstore)>",
                "<Book: Permutation City by Greg Egan (available at Angus and "
                "Robertson)>",
            ],
            transform=repr,
        )