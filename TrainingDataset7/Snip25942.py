def test_m2m_relations_signals_alternative_ways(self):
        expected_messages = []

        self._initialize_signal_car()

        # alternative ways of setting relation:
        self.vw.default_parts.create(name="Windows")
        p6 = Part.objects.get(name="Windows")
        expected_messages.append(
            {
                "instance": self.vw,
                "action": "pre_add",
                "reverse": False,
                "model": Part,
                "raw": False,
                "objects": [p6],
            }
        )
        expected_messages.append(
            {
                "instance": self.vw,
                "action": "post_add",
                "reverse": False,
                "model": Part,
                "raw": False,
                "objects": [p6],
            }
        )
        self.assertEqual(self.m2m_changed_messages, expected_messages)

        # direct assignment clears the set first, then adds
        self.vw.default_parts.set([self.wheelset, self.doors, self.engine])
        expected_messages.append(
            {
                "instance": self.vw,
                "action": "pre_remove",
                "reverse": False,
                "model": Part,
                "raw": False,
                "objects": [p6],
            }
        )
        expected_messages.append(
            {
                "instance": self.vw,
                "action": "post_remove",
                "reverse": False,
                "model": Part,
                "raw": False,
                "objects": [p6],
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