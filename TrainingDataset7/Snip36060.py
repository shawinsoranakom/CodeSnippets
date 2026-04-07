def test_run_loop_stop_and_return(self):
        def mocked_tick(*args):
            yield
            self.reloader.stop()
            return  # Raises StopIteration

        with mock.patch.object(self.reloader, "tick", side_effect=mocked_tick) as tick:
            self.reloader.run_loop()

        self.assertEqual(tick.call_count, 1)