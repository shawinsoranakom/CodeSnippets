def _test_join_base(
        self,
        uneven_inputs: bool,
        num_joinables: int,
        enable: bool,
        throw_on_early_termination: bool,
        num_allreduces: int,
        run_post_hooks: bool,
        expected_total: int | None = None,
    ):
        r"""
        Skeleton for all :class:`Join` tests.

        Arguments:
            uneven_inputs (bool): ``True`` to use uneven inputs; ``False``
                otherwise.
            num_joinables (int): number of :class:`AllReducer` s to construct.
            enable (bool): ``True`` to enable the join context manager;
                ``False`` otherwise.
            throw_on_early_termination (bool): ``True`` to raise an exception
                upon detecting uneven inputs; ``False`` otherwise.
            num_allreduces (int): number of all-reduces to perform per input.
            run_post_hooks (bool): ``True`` to run post-hooks; ``False``
                otherwise.
            expected_total (Optional[int]): ``None`` to not check the expected
                all-reduce total; otherwise, the expected total; default is
                ``None``.
        """
        self.dist_init(self.rank, self.world_size)

        allreducers = [
            AllReducer(self.device, self.process_group) for _ in range(num_joinables)
        ]
        for allreducer in allreducers:
            self.assertEqual(allreducer.post_hook_tensor.item(), BEFORE_CONSTANT)

        inputs = (
            self.construct_uneven_inputs(self.base_num_inputs, self.offset)
            if uneven_inputs
            else self.construct_even_inputs(self.base_num_inputs)
        )
        allreduce_total = 0

        # Expect a `RuntimeError` if `throw_on_early_termination=True`
        # Rank 0 exhausts its inputs first
        expected_msg = (
            "Rank 0 exhausted all inputs."
            if self.rank == 0
            else "Detected at least one rank that exhausted inputs. "
            "Throwing across all ranks."
        )
        with (
            self.assertRaisesRegex(RuntimeError, expected_msg)
            if throw_on_early_termination
            else contextlib.nullcontext()
        ):
            with Join(
                allreducers,
                enable=enable,
                throw_on_early_termination=throw_on_early_termination,
                num_allreduces=num_allreduces,
                run_post_hooks=run_post_hooks,
            ):
                for _ in inputs:
                    for allreducer in allreducers:
                        allreduce_total += allreducer(num_allreduces)

        if throw_on_early_termination:
            return

        # Check `expected_total` if not `None`
        if expected_total:
            self.assertEqual(allreduce_total, expected_total)

        # All `AllReduce` instances should receive the updated
        # `post_hook_tensor` from the last-joined process
        if run_post_hooks:
            for allreducer in allreducers:
                self.assertEqual(allreducer.post_hook_tensor.item(), AFTER_CONSTANT)