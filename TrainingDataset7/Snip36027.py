def test_swallows_keyboard_interrupt(self, mocked_get_reloader):
        mocked_get_reloader.side_effect = KeyboardInterrupt()
        autoreload.run_with_reloader(lambda: None)