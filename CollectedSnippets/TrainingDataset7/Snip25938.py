def test_m2m_relations_signals_reverse_relation_with_custom_related_name(self):
        self._initialize_signal_car()
        # remove airbag from the self.vw (reverse relation with custom
        # related_name)
        self.airbag.cars_optional.remove(self.vw)
        self.assertEqual(
            self.m2m_changed_messages,
            [
                {
                    "instance": self.airbag,
                    "action": "pre_remove",
                    "reverse": True,
                    "model": Car,
                    "raw": False,
                    "objects": [self.vw],
                },
                {
                    "instance": self.airbag,
                    "action": "post_remove",
                    "reverse": True,
                    "model": Car,
                    "raw": False,
                    "objects": [self.vw],
                },
            ],
        )