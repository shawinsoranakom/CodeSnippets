def test_doesnotexist_class(self):
        klass = Event.DoesNotExist
        self.assertIs(pickle.loads(pickle.dumps(klass)), klass)