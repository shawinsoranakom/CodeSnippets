def test_split_shards_random(self) -> None:
        random.seed(120)
        for _ in range(100):
            num_shards = random.randint(1, 10)
            num_tests = random.randint(1, 100)
            test_names = [str(i) for i in range(num_tests)]
            tests = [TestRun(x) for x in test_names]
            serial = [x for x in test_names if random.randint(0, 1) == 0]
            has_times = [x for x in test_names if random.randint(0, 1) == 0]
            random_times: dict[str, float] = {
                i: random.randint(0, THRESHOLD * 10) for i in has_times
            }
            sort_by_time = random.randint(0, 1) == 0

            shards = calculate_shards(
                num_shards,
                tests,
                random_times,
                None,
                must_serial=lambda x: x in serial,
                sort_by_time=sort_by_time,
            )

            times = [x[0] for x in shards]
            max_diff = max(times) - min(times)
            self.assertTrue(max_diff <= THRESHOLD + (num_tests - len(has_times)) * 60)

            all_sharded_tests: dict[str, list[ShardedTest]] = defaultdict(list)
            for _, sharded_tests in shards:
                for sharded_test in sharded_tests:
                    all_sharded_tests[sharded_test.name].append(sharded_test)

            # Check that all test files are represented in the shards
            self.assertListEqual(sorted(test_names), sorted(all_sharded_tests.keys()))
            # Check that for each test file, the pytest shards' times adds up to
            # original and all shards are present
            for test, sharded_tests in all_sharded_tests.items():
                if random_times.get(test) is None:
                    self.assertTrue(len(sharded_tests) == 1)
                    self.assertTrue(sharded_tests[0].time is None)
                else:
                    # x.time is not None because of the above check
                    self.assertAlmostEqual(
                        random_times[test],
                        sum(x.time for x in sharded_tests),  # type: ignore[misc]
                    )
                self.assertListEqual(
                    list(range(sharded_tests[0].num_shards)),
                    sorted(x.shard - 1 for x in sharded_tests),
                )
            # Check that sort_by_time is respected
            if sort_by_time:

                def comparator(a: ShardedTest, b: ShardedTest) -> int:
                    # serial comes first
                    if a.name in serial and b.name not in serial:
                        return -1
                    if a.name not in serial and b.name in serial:
                        return 1
                    # known test times come first
                    if a.time is not None and b.time is None:
                        return -1
                    if a.time is None and b.time is not None:
                        return 1
                    if a.time == b.time:
                        return 0
                    # not None due to the above checks
                    return -1 if a.time > b.time else 1  # type: ignore[operator]

            else:

                def comparator(a: ShardedTest, b: ShardedTest) -> int:
                    # serial comes first
                    if a.name in serial and b.name not in serial:
                        return -1
                    if a.name not in serial and b.name in serial:
                        return 1
                    return test_names.index(a.name) - test_names.index(b.name)

            for _, sharded_tests in shards:
                self.assertListEqual(
                    sorted(sharded_tests, key=functools.cmp_to_key(comparator)),
                    sharded_tests,
                )