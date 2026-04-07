def test_direct_instantiation(self):
        """
        It should be possible to use the view without going through .as_view()
        (#21564).
        """
        view = RedirectView()
        response = view.dispatch(self.rf.head("/foo/"))
        self.assertEqual(response.status_code, 410)