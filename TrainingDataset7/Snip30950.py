def test_order_by_model_with_abstract_inheritance_and_meta_ordering(self):
        group = Group.objects.create(name="test")
        event = MyEvent.objects.create(title="test event", group=group)
        event.edition_set.create()
        self.assert_pickles(event.edition_set.order_by("event"))