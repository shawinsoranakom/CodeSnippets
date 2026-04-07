def test_nowait_and_skip_locked(self):
        with self.assertRaisesMessage(
            ValueError, "The nowait option cannot be used with skip_locked."
        ):
            Person.objects.select_for_update(nowait=True, skip_locked=True)