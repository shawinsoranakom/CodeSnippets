def test_no_upgrade(self):
        encoded = make_password("lètmein")
        state = {"upgraded": False}

        def setter():
            state["upgraded"] = True

        self.assertFalse(check_password("WRONG", encoded, setter))
        self.assertFalse(state["upgraded"])