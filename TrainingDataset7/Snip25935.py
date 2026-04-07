def test_m2m_relations_add_remove_clear(self):
        expected_messages = []

        self._initialize_signal_car(add_default_parts_before_set_signal=True)

        self.vw.default_parts.add(self.wheelset, self.doors, self.engine)
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

        # give the BMW and Toyota some doors as well
        self.doors.car_set.add(self.bmw, self.toyota)
        expected_messages.append(
            {
                "instance": self.doors,
                "action": "pre_add",
                "reverse": True,
                "model": Car,
                "raw": False,
                "objects": [self.bmw, self.toyota],
            }
        )
        expected_messages.append(
            {
                "instance": self.doors,
                "action": "post_add",
                "reverse": True,
                "model": Car,
                "raw": False,
                "objects": [self.bmw, self.toyota],
            }
        )
        self.assertEqual(self.m2m_changed_messages, expected_messages)