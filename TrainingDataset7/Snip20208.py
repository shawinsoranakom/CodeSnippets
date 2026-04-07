def test_related_manager(self):
        """
        The related managers extend the default manager.
        """
        self.assertIsInstance(self.droopy.books, PublishedBookManager)
        self.assertIsInstance(self.b2.authors, PersonManager)