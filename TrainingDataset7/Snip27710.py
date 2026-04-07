def test_serialize_unbound_method_reference(self):
        """An unbound method used within a class body can be serialized."""
        self.serialize_round_trip(TestModel1.thing)