def test_optgroups(self):
        choices_dict = {
            "Audio": [
                ("vinyl", "Vinyl"),
                ("cd", "CD"),
            ],
            "Video": [
                ("vhs", "VHS Tape"),
                ("dvd", "DVD"),
            ],
            "unknown": "Unknown",
        }
        choices_list = list(choices_dict.items())
        choices_nested_dict = {
            k: dict(v) if isinstance(v, list) else v for k, v in choices_dict.items()
        }

        for choices in (choices_dict, choices_list, choices_nested_dict):
            with self.subTest(choices):
                self._test_optgroups(choices)