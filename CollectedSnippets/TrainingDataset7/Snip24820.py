def test_redirect_lazy(self):
        """Make sure HttpResponseRedirect works with lazy strings."""
        r = HttpResponseRedirect(lazystr("/redirected/"))
        self.assertEqual(r.url, "/redirected/")