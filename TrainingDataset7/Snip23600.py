def test_generic_reverse_relation_with_abc(self):
        """
        The reverse generic relation accessor (targets) is created if the
        GenericRelation comes from an abstract base model (HasLinks).
        """
        thing = HasLinkThing.objects.create()
        link = Link.objects.create(content_object=thing)
        self.assertCountEqual(link.targets.all(), [thing])