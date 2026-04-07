def test_manager_pickle(self):
        pickle.loads(pickle.dumps(Happening.objects))