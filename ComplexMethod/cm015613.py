def test_transformer_training(self, is_seq_parallel, dtype: torch.dtype):
        EXP_BASE_CC = ExpCommCounts(
            fwd={all_reduce: 6, all_gather: 1}, bwd={all_reduce: 9}
        )
        EXP_SEQ_PARALLEL_CC = ExpCommCounts(
            fwd={reduce_scatter: 6, all_gather: 6},
            bwd={reduce_scatter: 5, all_gather: 6},
            optim={all_reduce: 30},
        )

        # Disable dropout in the test since we cannot reproduce the same random
        # behaviors when comparing single-gpu models with multi-gpu models.
        model_args = ModelArgs(dropout_p=0.0)
        model = self._setup_single_gpu_model(
            model_args, dtype
        )  # Step 1: Initialize single-gpu models.
        model_tp = self._setup_tp_model(
            model, is_seq_parallel, dtype
        )  # Step 2: Setup tp model, place onto device mesh.
        optim, optim_tp = self._setup_optimizer(
            model, model_tp
        )  # Step 3: Setup optimizers for both models

        # Initialize input and make sure all ranks have the same input.
        inp_size = [8, 8]  # [batch_size, seq_len]
        if is_seq_parallel:
            if inp_size[1] % self.world_size != 0:
                raise AssertionError(
                    f"Expected inp_size[1] % world_size == 0, got {inp_size[1]} % {self.world_size}"
                )

        torch.manual_seed(0)
        steps = 10 if type(model) is torch.float64 else 1
        for _ in range(steps):
            inp = torch.randint(
                model_args.vocab_size, inp_size, device=self.device_type
            )
            expected_fwd_comms = (
                EXP_SEQ_PARALLEL_CC.fwd if is_seq_parallel else EXP_BASE_CC.fwd
            )
            output, output_tp = self._validate_fwd(
                model, model_tp, inp, expected_fwd_comms
            )
            expected_bwd_comms = (
                EXP_SEQ_PARALLEL_CC.bwd if is_seq_parallel else EXP_BASE_CC.bwd
            )
            self._validate_bwd(model, model_tp, output, output_tp, expected_bwd_comms)
            expected_optim_comms = (
                EXP_SEQ_PARALLEL_CC.optim if is_seq_parallel else EXP_BASE_CC.optim
            )
            self._validate_optim_step(
                model, model_tp, optim, optim_tp, expected_optim_comms
            )