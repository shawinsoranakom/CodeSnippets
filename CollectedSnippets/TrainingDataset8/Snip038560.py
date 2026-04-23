def test_call_assert(self):
        key = "mysection.myName"
        c = ConfigOption(key)

        with pytest.raises(AssertionError) as e:

            @c
            def someRandomFunction():
                pass

        self.assertEqual(
            "Complex config options require doc strings for their description.",
            str(e.value),
        )