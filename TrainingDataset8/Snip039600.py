def test_external_module(self):
        """Test code that references an external module."""

        # NB: If a future vegalite update removes the v3 API, these functions
        # will need to be updated!

        def call_altair_concat():
            return altair.vegalite.v4.api.concat()

        def call_altair_layer():
            return altair.vegalite.v4.api.layer()

        self.assertNotEqual(get_hash(call_altair_concat), get_hash(call_altair_layer))