def test_update_too_many_args(self):
        x = MultiValueDict({"a": []})
        msg = "update expected at most 1 argument, got 2"
        with self.assertRaisesMessage(TypeError, msg):
            x.update(1, 2)