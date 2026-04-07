def test_url_reverse_no_settings_module(self):
        """
        #9005 -- url tag shouldn't require settings.SETTINGS_MODULE to
        be set.
        """
        t = self._engine().from_string("{% url will_not_match %}")
        c = Context()
        with self.assertRaises(NoReverseMatch):
            t.render(c)