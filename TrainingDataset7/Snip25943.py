def test_m2m_relations_signals_clearing_removing(self):
        expected_messages = []

        self._initialize_signal_car(add_default_parts_before_set_signal=True)

        # set by clearing.
        self.vw.default_parts.set([self.wheelset, self.doors, self.engine], clear=True)
        expected_messages.append(
            {
                "instance": self.vw,
                "action": "pre_clear",
                "reverse": False,
                "model": Part,
                "raw": False,
            }
        )
        expected_messages.append(
            {
                "instance": self.vw,
                "action": "post_clear",
                "reverse": False,
                "model": Part,
                "raw": False,
            }
        )
        expected_messages.append(
            {
                "instance": self.vw,
                "action": "pre_add",
                "reverse": False,
                "model": Part,
                "raw": False,
                "objects": [self.doors, self.engine, self.wheelset],
            }
        )
        expected_messages.append(
            {
                "instance": self.vw,
                "action": "post_add",
                "reverse": False,
                "model": Part,
                "raw": False,
                "objects": [self.doors, self.engine, self.wheelset],
            }
        )
        self.assertEqual(self.m2m_changed_messages, expected_messages)

        # set by only removing what's necessary.
        self.vw.default_parts.set([self.wheelset, self.doors], clear=False)
        expected_messages.append(
            {
                "instance": self.vw,
                "action": "pre_remove",
                "reverse": False,
                "model": Part,
                "raw": False,
                "objects": [self.engine],
            }
        )
        expected_messages.append(
            {
                "instance": self.vw,
                "action": "post_remove",
                "reverse": False,
                "model": Part,
                "raw": False,
                "objects": [self.engine],
            }
        )
        self.assertEqual(self.m2m_changed_messages, expected_messages)