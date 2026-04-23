def test_get_data_none(self):
        msg = (
            "Cannot encode None for key 'value' in a query string. Did you "
            "mean to pass an empty string or omit the value?"
        )
        with self.assertRaisesMessage(TypeError, msg):
            self.client.get("/get_view/", {"value": None})