def test_vector_combined_mismatch(self):
        msg = (
            "SearchVector can only be combined with other SearchVector "
            "instances, got NoneType."
        )
        with self.assertRaisesMessage(TypeError, msg):
            Line.objects.filter(dialogue__search=None + SearchVector("character__name"))