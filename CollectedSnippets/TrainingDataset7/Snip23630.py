def test_dispatch_decoration(self):
        """
        Attributes set by decorators on the dispatch method
        are also present on the closure.
        """
        self.assertTrue(DecoratedDispatchView.as_view().is_decorated)