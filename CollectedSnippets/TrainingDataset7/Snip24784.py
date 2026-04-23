def test_mutable_delete(self):
        q = QueryDict(mutable=True)
        q["name"] = "john"
        del q["name"]
        self.assertNotIn("name", q)