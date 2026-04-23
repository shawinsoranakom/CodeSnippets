def test_lazy_base_url_init(self):
        """
        FileSystemStorage.__init__() shouldn't evaluate base_url.
        """
        storage = FileSystemStorage(base_url=reverse_lazy("app:url"))
        with self.assertRaises(NoReverseMatch):
            storage.url(storage.base_url)