def _test_cycle_lr(
        self,
        scheduler,
        lr_targets,
        momentum_targets,
        batch_iterations,
        verbose=False,
        use_beta1=False,
    ):
        for batch_num in range(batch_iterations):
            if verbose:
                if "momentum" in self.opt.param_groups[0]:
                    print(
                        "batch{}:\tlr={},momentum={}".format(
                            batch_num,
                            self.opt.param_groups[0]["lr"],
                            self.opt.param_groups[0]["momentum"],
                        )
                    )
                elif use_beta1 and "betas" in self.opt.param_groups[0]:
                    print(
                        "batch{}:\tlr={},beta1={}".format(
                            batch_num,
                            self.opt.param_groups[0]["lr"],
                            self.opt.param_groups[0]["betas"][0],
                        )
                    )
                else:
                    print(
                        "batch{}:\tlr={}".format(
                            batch_num, self.opt.param_groups[0]["lr"]
                        )
                    )

            for param_group, lr_target, momentum_target in zip(
                self.opt.param_groups, lr_targets, momentum_targets
            ):
                self.assertEqual(
                    lr_target[batch_num],
                    param_group["lr"],
                    msg="LR is wrong in batch_num {}: expected {}, got {}".format(
                        batch_num, lr_target[batch_num], param_group["lr"]
                    ),
                    atol=1e-5,
                    rtol=0,
                )

                if use_beta1 and "betas" in param_group:
                    self.assertEqual(
                        momentum_target[batch_num],
                        param_group["betas"][0],
                        msg="Beta1 is wrong in batch_num {}: expected {}, got {}".format(
                            batch_num,
                            momentum_target[batch_num],
                            param_group["betas"][0],
                        ),
                        atol=1e-5,
                        rtol=0,
                    )
                elif "momentum" in param_group:
                    self.assertEqual(
                        momentum_target[batch_num],
                        param_group["momentum"],
                        msg="Momentum is wrong in batch_num {}: expected {}, got {}".format(
                            batch_num,
                            momentum_target[batch_num],
                            param_group["momentum"],
                        ),
                        atol=1e-5,
                        rtol=0,
                    )
            self.opt.step()
            scheduler.step()