def test_forward_relatedobjectdoesnotexist_class(self):
        # ForwardManyToOneDescriptor
        klass = Event.group.RelatedObjectDoesNotExist
        self.assertIs(pickle.loads(pickle.dumps(klass)), klass)
        # ForwardOneToOneDescriptor
        klass = Happening.event.RelatedObjectDoesNotExist
        self.assertIs(pickle.loads(pickle.dumps(klass)), klass)