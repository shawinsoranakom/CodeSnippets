def test_url_reverse_view_name(self):
        """
        #19827 -- url tag should keep original stack trace when reraising
        exception.
        """
        t = self._engine().from_string("{% url will_not_match %}")
        c = Context()
        try:
            t.render(c)
        except NoReverseMatch:
            tb = sys.exc_info()[2]
            depth = 0
            while tb.tb_next is not None:
                tb = tb.tb_next
                depth += 1
            self.assertGreater(
                depth, 5, "The traceback context was lost when reraising the traceback."
            )