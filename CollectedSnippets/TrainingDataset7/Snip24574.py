def test_07b_values(self):
        "Testing values() and values_list() with aware datetime. See #21565."
        Event.objects.create(name="foo", when=timezone.now())
        list(Event.objects.values_list("when"))