def test_cycle_lr_triangular2_mode_step_size_up_down(self):
        lr_base_target = [
            1.0,
            3.0,
            5.0,
            13.0 / 3,
            11.0 / 3,
            9.0 / 3,
            7.0 / 3,
            5.0 / 3,
            1.0,
            2.0,
            3.0,
            8.0 / 3,
            7.0 / 3,
            6.0 / 3,
            5.0 / 3,
            4.0 / 3,
            1.0,
            3.0 / 2,
            2.0,
            11.0 / 6,
            10.0 / 6,
            9.0 / 6,
            8.0 / 6,
            7.0 / 6,
        ]
        momentum_base_target = [
            5.0,
            3.0,
            1.0,
            5.0 / 3,
            7.0 / 3,
            3.0,
            11.0 / 3,
            13.0 / 3,
            5.0,
            4.0,
            3.0,
            10.0 / 3,
            11.0 / 3,
            4.0,
            13.0 / 3,
            14.0 / 3,
            5.0,
            4.5,
            4.0,
            25.0 / 6,
            13.0 / 3,
            4.5,
            14.0 / 3,
            29.0 / 6,
        ]
        deltas = [2 * i for i in range(2)]
        base_lrs = [1 + delta for delta in deltas]
        max_lrs = [5 + delta for delta in deltas]
        lr_targets = [[x + delta for x in lr_base_target] for delta in deltas]
        momentum_targets = [
            [x + delta for x in momentum_base_target] for delta in deltas
        ]
        scheduler = CyclicLR(
            self.opt,
            base_lr=base_lrs,
            max_lr=max_lrs,
            step_size_up=2,
            step_size_down=6,
            cycle_momentum=True,
            base_momentum=base_lrs,
            max_momentum=max_lrs,
            mode="triangular2",
        )
        self._test_cycle_lr(
            scheduler, lr_targets, momentum_targets, len(lr_base_target)
        )