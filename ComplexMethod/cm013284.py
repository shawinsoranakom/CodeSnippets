def _test_DDP_niter(
            self,
            model_base,
            model_DDP,
            input,
            target,
            loss,
            local_bs,
            rank,
            batch_size,
            test_save,
            offset=None,
            world_size=0,
            zero_grad=False,
            memory_format=None,
            n_iter=5,
        ):
            for idx in range(n_iter):
                # single cpu/gpu training
                self._test_DDP_helper(
                    model_base, input, target, loss, memory_format=memory_format
                )

                if offset is None:
                    offset = rank * local_bs

                # DDP training, DDP scatters subsets of input_cpu to nodes/GPUs
                self._test_DDP_helper(
                    model_DDP,
                    input[offset : offset + local_bs],
                    target[offset : offset + local_bs],
                    loss,
                    world_size * local_bs / batch_size if world_size != 0 else 1,
                    memory_format=memory_format,
                )

                # Update weights and run a second iteration to shake out errors
                if zero_grad:
                    self._model_step_with_zero_grad(model_base)
                    self._model_step_with_zero_grad(model_DDP)
                else:
                    self._model_step(model_base)
                    self._model_step(model_DDP)
                self._assert_equal_param(
                    list(model_base.parameters()), list(model_DDP.module.parameters())
                )

                # Shuffle the input so that DDP input is different
                input = input[torch.randperm(batch_size)]

                # save the model in the middle and reload
                if test_save and idx == 2 and INIT_METHOD.startswith("file://"):
                    with tempfile.NamedTemporaryFile() as tmp:
                        if sys.platform == "win32":
                            torch.save(model_DDP, tmp)
                            tmp.seek(0)
                            # weights_only=False as this is legacy code that saves the model
                            model_DDP = torch.load(tmp, weights_only=False)
                        else:
                            torch.save(model_DDP, tmp.name)
                            # weights_only=False as this is legacy code that saves the model
                            model_DDP = torch.load(tmp.name, weights_only=False)

            with tempfile.TemporaryFile() as tmp_file:
                torch.save(model_DDP, tmp_file)
                tmp_file.seek(0)
                # weights_only=False as this is legacy code that saves the model
                saved_model = torch.load(tmp_file, weights_only=False)
            for k in model_DDP.state_dict():
                self.assertEqual(model_DDP.state_dict()[k], saved_model.state_dict()[k])