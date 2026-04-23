def test_bug14894_translation_activate_thread_safety(self):
        translation_count = len(trans_real._translations)
        # May raise RuntimeError if translation.activate() isn't thread-safe.
        translation.activate("pl")
        # make sure sideeffect_str actually added a new translation
        self.assertLess(translation_count, len(trans_real._translations))