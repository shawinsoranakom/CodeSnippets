def test_m2m_relations_set_base_raw(self):
        self.chuck.idols.add(self.daisy)
        self._initialize_signal_person()
        self.chuck.idols.set_base([self.alice, self.bob], raw=True)
        self.assertEqual(
            self.m2m_changed_messages,
            [
                {
                    "instance": self.chuck,
                    "action": "pre_remove",
                    "reverse": True,
                    "model": Person,
                    "raw": True,
                    "objects": [self.daisy],
                },
                {
                    "instance": self.chuck,
                    "action": "post_remove",
                    "reverse": True,
                    "model": Person,
                    "raw": True,
                    "objects": [self.daisy],
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