def test_fetch_mode_fetch_one(self):
        restored = pickle.loads(pickle.dumps(self.happening))
        self.assertIs(restored._state.fetch_mode, models.FETCH_ONE)