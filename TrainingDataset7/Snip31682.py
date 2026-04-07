def setUp(self):
        self.object_list = [
            {"pk": 1, "model": "serializers.author", "fields": {"name": "Jane"}},
            {"pk": 2, "model": "serializers.author", "fields": {"name": "Joe"}},
        ]
        self.deserializer = Deserializer(self.object_list)
        self.jane = Author(name="Jane", pk=1)
        self.joe = Author(name="Joe", pk=2)