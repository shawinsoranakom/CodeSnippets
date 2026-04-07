def test_m2m_relations_set_base_raw_clear(self):
        self.chuck.idols.set([self.daisy, self.bob])
        self._initialize_signal_person()
        self.chuck.idols.set_base([self.alice, self.bob], clear=True, raw=True)
        self.assertEqual(
            self.m2m_changed_messages,
            [
                {
                    "instance": self.chuck,
                    "action": "pre_clear",
                    "reverse": True,
                    "model": Person,
                    "raw": True,
                },
                {
                    "instance": self.chuck,
                    "action": "post_clear",
                    "reverse": True,
                    "model": Person,
                    "raw": True,
                },
                {
                    "instance": self.chuck,
                    "action": "pre_add",
                    "reverse": True,
                    "model": Person,
                    "raw": True,
                    "objects": [self.alice, self.bob],
                },
                {
                    "instance": self.chuck,
                    "action": "post_add",
                    "reverse": True,
                    "model": Person,
                    "raw": True,
                    "objects": [self.alice, self.bob],
                },
            ],
        )