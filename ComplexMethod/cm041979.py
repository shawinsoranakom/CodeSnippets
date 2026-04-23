async def run(self, role: "STRole", wake_up_hour: int):
        hour_str = [
            "00:00 AM",
            "01:00 AM",
            "02:00 AM",
            "03:00 AM",
            "04:00 AM",
            "05:00 AM",
            "06:00 AM",
            "07:00 AM",
            "08:00 AM",
            "09:00 AM",
            "10:00 AM",
            "11:00 AM",
            "12:00 PM",
            "01:00 PM",
            "02:00 PM",
            "03:00 PM",
            "04:00 PM",
            "05:00 PM",
            "06:00 PM",
            "07:00 PM",
            "08:00 PM",
            "09:00 PM",
            "10:00 PM",
            "11:00 PM",
        ]
        n_m1_activity = []
        diversity_repeat_count = 1  # TODO mg 1->3
        for i in range(diversity_repeat_count):
            logger.info(f"diversity_repeat_count idx: {i}")
            n_m1_activity_set = set(n_m1_activity)
            if len(n_m1_activity_set) < 5:
                n_m1_activity = []
                for count, curr_hour_str in enumerate(hour_str):
                    if wake_up_hour > 0:
                        n_m1_activity += ["sleeping"]
                        wake_up_hour -= 1
                    else:
                        logger.info(f"_generate_schedule_for_given_hour idx: {count}, n_m1_activity: {n_m1_activity}")
                        n_m1_activity += [
                            await self._generate_schedule_for_given_hour(role, curr_hour_str, n_m1_activity, hour_str)
                        ]

        # Step 1. Compressing the hourly schedule to the following format:
        # The integer indicates the number of hours. They should add up to 24.
        # [['sleeping', 6], ['waking up and starting her morning routine', 1],
        # ['eating breakfast', 1], ['getting ready for the day', 1],
        # ['working on her painting', 2], ['taking a break', 1],
        # ['having lunch', 1], ['working on her painting', 3],
        # ['taking a break', 2], ['working on her painting', 2],
        # ['relaxing and watching TV', 1], ['going to bed', 1], ['sleeping', 2]]
        _n_m1_hourly_compressed = []
        prev = None
        prev_count = 0
        for i in n_m1_activity:
            if i != prev:
                prev_count = 1
                _n_m1_hourly_compressed += [[i, prev_count]]
                prev = i
            elif _n_m1_hourly_compressed:
                _n_m1_hourly_compressed[-1][1] += 1

        # Step 2. Expand to min scale (from hour scale)
        # [['sleeping', 360], ['waking up and starting her morning routine', 60],
        # ['eating breakfast', 60],..
        n_m1_hourly_compressed = []
        for task, duration in _n_m1_hourly_compressed:
            n_m1_hourly_compressed += [[task, duration * 60]]
        logger.info(f"Role: {role.name} Action: {self.cls_name} output: {n_m1_hourly_compressed}")
        return n_m1_hourly_compressed