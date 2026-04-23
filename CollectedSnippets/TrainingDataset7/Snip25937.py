def test_m2m_relations_signals_give_the_self_vw_some_optional_parts(self):
        expected_messages = []

        self._initialize_signal_car()

        # give the self.vw some optional parts (second relation to same model)
        self.vw.optional_parts.add(self.airbag, self.sunroof)
        expected_messages.append(
            {
                "instance": self.vw,
                "action": "pre_add",
                "reverse": False,
                "model": Part,
                "raw": False,
                "objects": [self.airbag, self.sunroof],
            }
        )
        expected_messages.append(
            {
                "instance": self.vw,
                "action": "post_add",
                "reverse": False,
                "model": Part,
                "raw": False,
                "objects": [self.airbag, self.sunroof],
            }
        )
        self.assertEqual(self.m2m_changed_messages, expected_messages)

        # add airbag to all the cars (even though the self.vw already has one)
        self.airbag.cars_optional.add(self.vw, self.bmw, self.toyota)
        expected_messages.append(
            {
                "instance": self.airbag,
                "action": "pre_add",
                "reverse": True,
                "model": Car,
                "raw": False,
                "objects": [self.bmw, self.toyota],
            }
        )
        expected_messages.append(
            {
                "instance": self.airbag,
                "action": "post_add",
                "reverse": True,
                "model": Car,
                "raw": False,
                "objects": [self.bmw, self.toyota],
            }
        )
        self.assertEqual(self.m2m_changed_messages, expected_messages)