def test_m2m_relations_signals_reverse_relation(self):
        self._initialize_signal_car()
        # take all the airbags off of cars (clear reverse relation with custom
        # related_name)
        self.airbag.cars_optional.clear()
        self.assertEqual(
            self.m2m_changed_messages,
            [
                {
                    "instance": self.airbag,
                    "action": "pre_clear",
                    "reverse": True,
                    "model": Car,
                    "raw": False,
                },
                {
                    "instance": self.airbag,
                    "action": "post_clear",
                    "reverse": True,
                    "model": Car,
                    "raw": False,
                },
            ],
        )