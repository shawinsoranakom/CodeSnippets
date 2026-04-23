def test_subclasses_with_parent_gen_rel(self):
        """
        Generic relations on a base class (Vegetable) work correctly in
        subclasses (Carrot).
        """
        bear = Carrot.objects.create(name="carrot")
        TaggedItem.objects.create(content_object=bear, tag="orange")
        self.assertEqual(Carrot.objects.get(tags__tag="orange"), bear)