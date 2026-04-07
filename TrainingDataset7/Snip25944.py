def test_m2m_relations_signals_when_inheritance(self):
        expected_messages = []

        self._initialize_signal_car(add_default_parts_before_set_signal=True)

        # Signals still work when model inheritance is involved
        c4 = SportsCar.objects.create(name="Bugatti", price="1000000")
        c4b = Car.objects.get(name="Bugatti")
        c4.default_parts.set([self.doors])
        expected_messages.append(
            {
                "instance": c4,
                "action": "pre_add",
                "reverse": False,
                "model": Part,
                "raw": False,
                "objects": [self.doors],
            }
        )
        expected_messages.append(
            {
                "instance": c4,
                "action": "post_add",
                "reverse": False,
                "model": Part,
                "raw": False,
                "objects": [self.doors],
            }
        )
        self.assertEqual(self.m2m_changed_messages, expected_messages)

        self.engine.car_set.add(c4)
        expected_messages.append(
            {
                "instance": self.engine,
                "action": "pre_add",
                "reverse": True,
                "model": Car,
                "raw": False,
                "objects": [c4b],
            }
        )
        expected_messages.append(
            {
                "instance": self.engine,
                "action": "post_add",
                "reverse": True,
                "model": Car,
                "raw": False,
                "objects": [c4b],
            }
        )
        self.assertEqual(self.m2m_changed_messages, expected_messages)