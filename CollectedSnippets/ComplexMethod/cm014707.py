def test_peak_memory_foreach(self, device, dtype, optim_info):
        nparams = 10
        optim_inputs = optim_info.optim_inputs_func(device=device)
        optim_cls = optim_info.optim_cls
        for optim_input in optim_inputs:
            kwargs = deepcopy(optim_input.kwargs)
            max_mems = []
            for flag_value in (False, True):
                kwargs["foreach"] = flag_value
                # The 16 * 8 = 128 is critical here! Our CUDACachingAllocator allocates in blocks
                # of 512, meaning any tensor that occupies <512 bytes of memory will allocate a
                # whole 512 bytes anyway. We use 128 (cuz datasize would be 4 bytes) so that param
                # is size 512 exactly, making our later calculations for intermediate_size easy.
                param = torch.rand(16, 8, device=device, dtype=dtype)
                params = [torch.rand_like(param) for _ in range(nparams)]

                optimizer = optim_cls(params, **kwargs)

                for p in params:
                    p.grad = torch.rand_like(p)

                optimizer.step()
                import gc

                gc.collect()
                torch.cuda.reset_peak_memory_stats()
                optimizer.step()
                gc.collect()
                max_mems.append(torch.cuda.max_memory_allocated())

            st_max_mem, mt_max_mem = max_mems
            intermediate_size = nparams * param.nelement() * param.element_size()
            nintermediates = 1  # we expect a budget of 1 intermediate most of the time

            # Check the param group directly to handle if the compiler set capturable
            if optimizer.param_groups[0].get(
                "capturable", False
            ) or optim_cls.__name__ in ["Adadelta", "ASGD", "RAdam"]:
                # with capturable in Adam(W), we have 2 extra intermediates for the bias_corrections
                # with Adadelta, we have 2 extra for (acc_delta + eps) and (square_avg + eps)
                # ASGD allocates axs, 2x mus, 2x etas, and grads at the same time
                nintermediates = 3
                if optim_cls.__name__ == "NAdam":
                    # with capturable in NAdam, we have 3 extra intermediates for the
                    # bias_correction, mus, and mu_nexts
                    if TEST_WITH_TORCHDYNAMO:
                        # With dynamo, the eager/FX backend appears to hold memory longer than
                        # vanilla eager: https://github.com/pytorch/pytorch/issues/125511
                        nintermediates = 8
                    else:
                        nintermediates = 5

                if optim_cls.__name__ == "RAdam":
                    # RAdam has four intermediates with capturable
                    # num, unrect_step_size, buffer, grouped_grads
                    if TEST_WITH_TORCHDYNAMO:
                        # With dynamo, the eager/FX backend appears to hold memory than
                        # vanilla eager: https://github.com/pytorch/pytorch/issues/125511
                        nintermediates = 6
                    else:
                        nintermediates = 4

            elif optim_cls.__name__ in ["NAdam", "Adagrad", "RMSprop", "Adafactor"]:
                # NAdam uses two intermediates at the same time (grads & exp_avg_sq_sqrt)
                # Adagrad uses std and grads at the same time
                # RMSprop uses avg and grads
                # Adafactor uses row/col var and its mean
                nintermediates = 2

                if optim_cls.__name__ == "Adafactor" and kwargs.get("maximize", False):
                    # When maximize is True, Adafactor also tracks device_grad
                    nintermediates = 3

            # Dynamo ST uses less mem than eager in the case of Adam/Adagrad/Nadam/RAdam
            # which makes the foreach memory check fail
            if TEST_WITH_TORCHDYNAMO:
                st_max_mem += 6000

            expected_max_mem = st_max_mem + intermediate_size * nintermediates
            # hipcc currently can't generate efficient code for the small buffer optimization
            # code path (see Note [small buffer optimization] for details), thus we always
            # dynamically allocate the tensor metadata for ROCM. Adjusting the expected max
            # memory usage to account for this.
            if TEST_WITH_ROCM:
                expected_max_mem *= 1.02

            self.assertLessEqual(mt_max_mem, expected_max_mem)