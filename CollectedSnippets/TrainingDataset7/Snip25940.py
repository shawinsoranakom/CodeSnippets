def test_m2m_relations_signals_all_the_doors_off_of_cars(self):
        self._initialize_signal_car()
        # take all the doors off of cars
        self.doors.car_set.clear()
        self.assertEqual(
            self.m2m_changed_messages,
            [
                {
                    "instance": self.doors,
                    "action": "pre_clear",
                    "reverse": True,
                    "model": Car,
                    "raw": False,
                },
                {
                    "instance": self.doors,
                    "action": "post_clear",
                    "reverse": True,
                    "model": Car,
                    "raw": False,
                },
            ],
        )