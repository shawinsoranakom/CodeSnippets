def test_base_view_class_is_sync(self):
        """
        View and by extension any subclasses that don't define handlers are
        sync.
        """
        self.assertIs(View.view_is_async, False)