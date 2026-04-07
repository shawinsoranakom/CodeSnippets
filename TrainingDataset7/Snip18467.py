def test_outer_wrapper_blocks(self):
        def blocker(*args):
            pass

        wrapper = self.mock_wrapper()
        c = connection  # This alias shortens the next line.
        with (
            c.execute_wrapper(wrapper),
            c.execute_wrapper(blocker),
            c.execute_wrapper(wrapper),
        ):
            with c.cursor() as cursor:
                cursor.execute("The database never sees this")
                self.assertEqual(wrapper.call_count, 1)
                cursor.executemany("The database never sees this %s", [("either",)])
                self.assertEqual(wrapper.call_count, 2)