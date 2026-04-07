def test_m2m_relations_signals_remove_relation(self):
        self._initialize_signal_car()
        # remove the engine from the self.vw and the airbag (which is not set
        # but is returned)
        self.vw.default_parts.remove(self.engine, self.airbag)
        self.assertEqual(
            self.m2m_changed_messages,
            [
                {
                    "instance": self.vw,
                    "action": "pre_remove",
                    "reverse": False,
                    "model": Part,
                    "raw": False,
                    "objects": [self.airbag, self.engine],
                },
                {
                    "instance": self.vw,
                    "action": "post_remove",
                    "reverse": False,
                    "model": Part,
                    "raw": False,
                    "objects": [self.airbag, self.engine],
                },
            ],
        )