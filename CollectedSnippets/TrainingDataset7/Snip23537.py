def test_subclasses_with_gen_rel(self):
        """
        Concrete model subclasses with generic relations work
        correctly (ticket 11263).
        """
        granite = Rock.objects.create(name="granite", hardness=5)
        TaggedItem.objects.create(content_object=granite, tag="countertop")
        self.assertEqual(Rock.objects.get(tags__tag="countertop"), granite)