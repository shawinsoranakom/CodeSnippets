def test_m2m_relations_signals_clear_all_parts_of_the_self_vw(self):
        self._initialize_signal_car()
        # clear all parts of the self.vw
        self.vw.default_parts.clear()
        self.assertEqual(
            self.m2m_changed_messages,
            [
                {
                    "instance": self.vw,
                    "action": "pre_clear",
                    "reverse": False,
                    "model": Part,
                    "raw": False,
                },
                {
                    "instance": self.vw,
                    "action": "post_clear",
                    "reverse": False,
                    "model": Part,
                    "raw": False,
                },
            ],
        )