def test_fetch_mode_fetch_peers(self):
        Happening.objects.create()
        objs = list(Happening.objects.fetch_mode(models.FETCH_PEERS))
        self.assertEqual(objs[0]._state.fetch_mode, models.FETCH_PEERS)
        self.assertEqual(len(objs[0]._state.peers), 2)

        restored = pickle.loads(pickle.dumps(objs))

        self.assertIs(restored[0]._state.fetch_mode, models.FETCH_PEERS)
        # Peers not restored because weak references are not picklable.
        self.assertEqual(restored[0]._state.peers, ())