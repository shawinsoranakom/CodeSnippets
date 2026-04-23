def test_post_data_none(self):
        msg = (
            "Cannot encode None for key 'value' as POST data. Did you mean "
            "to pass an empty string or omit the value?"
        )
        with self.assertRaisesMessage(TypeError, msg):
            self.client.post("/post_view/", {"value": None})