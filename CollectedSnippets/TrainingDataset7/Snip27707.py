def test_serialize_empty_nonempty_tuple(self):
        """
        Ticket #22679: makemigrations generates invalid code for (an empty
        tuple) default_permissions = ()
        """
        empty_tuple = ()
        one_item_tuple = ("a",)
        many_items_tuple = ("a", "b", "c")
        self.assertSerializedEqual(empty_tuple)
        self.assertSerializedEqual(one_item_tuple)
        self.assertSerializedEqual(many_items_tuple)