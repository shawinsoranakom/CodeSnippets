def setUpTestData(cls):
        SimpleItem.objects.create(name="test", value=42)
        cls.deferred_item = SimpleItem.objects.defer("value").first()
        cls.deferred_item.pk = None
        cls.deferred_item._state.adding = True
        cls.expected_msg = (
            "Cannot retrieve deferred field 'value' from an unsaved model."
        )