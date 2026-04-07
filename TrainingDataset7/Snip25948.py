def test_m2m_relations_with_self_add_idols(self):
        self._initialize_signal_person()
        self.chuck.idols.set([self.alice, self.bob])
        self.assertEqual(
            self.m2m_changed_messages,
            [
                {
                    "instance": self.chuck,
                    "action": "pre_add",
                    "reverse": True,
                    "model": Person,
                    "raw": False,
                    "objects": [self.alice, self.bob],
                },
                {
                    "instance": self.chuck,
                    "action": "post_add",
                    "reverse": True,
                    "model": Person,
                    "raw": False,
                    "objects": [self.alice, self.bob],
                },
            ],
        )