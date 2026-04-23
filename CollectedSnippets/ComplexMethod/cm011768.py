def bisect(self, num_attempts: int = 100, p: float = 0.5) -> list[ConfigType]:
        """
        Test configs and bisect to minimal failing configuration.
        """
        print(f"Starting random testing with bisection, seed {self.seed}, and p {p}")
        random.seed(self.seed)
        self._reset_configs()
        results = ResultType()
        ret: list[ConfigType] = []

        for attempt in range(num_attempts):
            print(f"Random attempt {attempt + 1}/{num_attempts}")

            config = self.new_config()

            for field_name, config_entry in self.fields.items():
                if (
                    field_name not in config
                    and not field_name.startswith("_")
                    and "TESTING_ONLY" not in field_name
                    and random.random() < p
                ):
                    value = self.sample(
                        field_name, config_entry.value_type, config_entry.default
                    )
                    config[field_name] = value

            status = self.test_config(results, config)
            if status not in OrderedSet([Status.PASSED, Status.SKIPPED]):
                if minimal_failing_config := self._bisect_failing_config(
                    results, config
                ):
                    print(f"Minimum failing config: {minimal_failing_config}")
                    ret.append(minimal_failing_config)

        return ret