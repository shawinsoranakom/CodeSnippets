def test_fetch_mode_raise(self):
        objs = list(Happening.objects.fetch_mode(models.RAISE))
        self.assertEqual(objs[0]._state.fetch_mode, models.RAISE)

        restored = pickle.loads(pickle.dumps(objs))
        self.assertIs(restored[0]._state.fetch_mode, models.RAISE)