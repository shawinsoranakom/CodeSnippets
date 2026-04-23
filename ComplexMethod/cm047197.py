def launch_perf_set(
        self,
        code: str, *,
        record_list: list[BaseModel] | None = None,
        relative_size: list[int] | None = None,
        check_type: Literal['linear'] | None = 'linear',
        number: int = 4,
        **kw,
    ):
        # initialize the record list with the children records
        if not record_list:
            record_list = self.get_test_children()
        # relative sizes are initialized to 1, 10, 100, ...
        relative_sizes = relative_size or [10 ** i for i in range(len(record_list))]
        assert len(relative_sizes) == len(record_list)
        repeat = 3
        results = [
            self.launch_perf(code, records=records, relative_size=relative_size, repeat=repeat, number=number, **kw)
            for records, relative_size in zip(record_list, relative_sizes)
        ]
        # checks
        if len(results) <= 3:
            check_type = None
        if check_type == 'linear':
            # approximative check that the resulting runs are behaving linearly
            # skip the first result as it is very small and not comparable
            check_results = [r / s for r, s in zip(results, relative_sizes)][1:]
            min_time = check_results[0]  # take the time for the first check result as a comparison point
            max_time = max(check_results)
            # just check that the biggest difference of timings per record
            # compared to minimum run time is not greater than the max_tolerance
            max_tolerance = 2.5
            _logger.info("%s Linear behaviour for %s", max_time / min_time < max_tolerance, check_results)
        else:
            self.assertFalse(check_type, "Unsupported check_type")
        return results