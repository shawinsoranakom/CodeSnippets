def test_invalid_redirect_repr(self):
        """
        If HttpResponseRedirect raises DisallowedRedirect, its __repr__()
        should work (in the debug view, for example).
        """
        response = HttpResponseRedirect.__new__(HttpResponseRedirect)
        with self.assertRaisesMessage(
            DisallowedRedirect, "Unsafe redirect to URL with protocol 'ssh'"
        ):
            HttpResponseRedirect.__init__(response, "ssh://foo")
        expected = (
            '<HttpResponseRedirect status_code=302, "text/html; charset=utf-8", '
            'url="ssh://foo">'
        )
        self.assertEqual(repr(response), expected)