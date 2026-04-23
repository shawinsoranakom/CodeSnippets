def test_multipleobjectsreturned_class(self):
        klass = Event.MultipleObjectsReturned
        self.assertIs(pickle.loads(pickle.dumps(klass)), klass)