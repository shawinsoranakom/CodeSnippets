def test_not_updated_class(self):
        klass = Event.NotUpdated
        self.assertIs(pickle.loads(pickle.dumps(klass)), klass)