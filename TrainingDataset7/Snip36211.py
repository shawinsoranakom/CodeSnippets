def test_child_not_a_dict_raises_typeerror(self):
        parent = {"bad": "not_a_dict"}
        sub = DeferredSubDict(parent, "bad")
        with self.assertRaises(TypeError):
            sub["any_key"]