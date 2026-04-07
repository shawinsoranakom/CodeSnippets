def test_each_object_should_have_auto_created(self):
        self.assertTrue(
            all(
                f.auto_created.__class__ == bool
                for f in self.fields_and_reverse_objects
            )
        )