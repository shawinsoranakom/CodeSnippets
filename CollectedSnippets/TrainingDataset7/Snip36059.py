def test_run_loop_catches_stopiteration(self):
        def mocked_tick():
            yield

        with mock.patch.object(self.reloader, "tick", side_effect=mocked_tick) as tick:
            self.reloader.run_loop()
        self.assertEqual(tick.call_count, 1)