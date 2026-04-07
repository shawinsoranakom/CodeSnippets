def test_m2m_relations_with_self_add_fan(self):
        self._initialize_signal_person()
        self.alice.fans.set([self.daisy])
        self.assertEqual(
            self.m2m_changed_messages,
            [
                {
                    "instance": self.alice,
                    "action": "pre_add",
                    "reverse": False,
                    "model": Person,
                    "raw": False,
                    "objects": [self.daisy],
                },
                {
                    "instance": self.alice,
                    "action": "post_add",
                    "reverse": False,
                    "model": Person,
                    "raw": False,
                    "objects": [self.daisy],
                },
            ],
        )