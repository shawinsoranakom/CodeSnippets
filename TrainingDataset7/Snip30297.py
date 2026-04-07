def test_too_many_concrete_classes(self):
        msg = (
            "Proxy model 'TooManyBases' has more than one non-abstract model base "
            "class."
        )
        with self.assertRaisesMessage(TypeError, msg):

            class TooManyBases(User, Person):
                class Meta:
                    proxy = True