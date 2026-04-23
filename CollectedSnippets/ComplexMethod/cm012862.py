def optimize_adaptive_rounding(
        self,
        module: torch.nn.Module,
        q_module: torch.nn.Module,
        activation: Callable[[torch.Tensor], torch.Tensor] | None = None,
    ) -> None:
        ada_quantizer = AdaroundFakeQuantizer(
            dtype=self.dtype,
            observer=self.observer,
            qscheme=self.qscheme,
            quant_min=self.quant_min,
            quant_max=self.quant_max,
            reduce_range=False,
        )
        ada_quantizer.enable_observer()
        ada_quantizer(q_module.weight)
        ada_quantizer.disable_observer()
        ada_quantizer.enable_fake_quant()
        optimizer = torch.optim.Adam([ada_quantizer.V])
        inp, out, fp_in = self.get_data_inp_out(module, q_module, self.data)

        print("==================== Before adaround ====================")
        if torch.abs(out[0] - module(fp_in[0])).sum().item() != 0:
            raise AssertionError(
                "In-placed activation is detected, please do not use activation in-placed"
            )
        # Stack the tensors in each list into a single tensor
        # Assuming inp and out are your lists of tensors
        inp_tensor = torch.vstack(inp)
        out_tensor = torch.vstack(out)
        dataset = TensorDataset(inp_tensor, out_tensor)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        self._compute_and_display_local_losses(ada_quantizer, q_module, inp[0], out[0])
        global_idx = 0
        one_iter = len(out) // self.batch_size
        for iteration in range(self.max_iter // one_iter):
            reconstruction_loss = regularization_loss = torch.tensor(0)
            for q_inp, fp_out in dataloader:
                optimizer.zero_grad()
                q_weight = ada_quantizer(q_module.weight)
                if isinstance(module, torch.nn.Conv1d):
                    q_out = torch.nn.functional.conv1d(  # type: ignore[call-overload, misc]
                        q_inp,
                        q_weight,
                        bias=q_module.bias,
                        stride=q_module.stride,
                        padding=q_module.padding,
                        dilation=q_module.dilation,
                        groups=q_module.groups,
                    )
                elif isinstance(q_module, torch.nn.Linear):
                    q_out = torch.nn.functional.linear(
                        q_inp,
                        q_weight,
                        bias=q_module.bias,
                    )
                else:
                    raise NotImplementedError
                regularization_loss, reconstruction_loss = self.adaptive_round_loss_fn(
                    fp_out,
                    q_out,
                    ada_quantizer.V,
                    curr_iter=global_idx,
                )
                loss = regularization_loss + reconstruction_loss
                loss.backward()
                optimizer.step()
                global_idx += 1
                if global_idx >= self.max_iter:
                    break
            if global_idx >= self.max_iter:
                break
            if iteration % 30 == 0:
                print(
                    f"glob iter {global_idx} regularization_loss {regularization_loss.item()} "
                    f"reconstruction_loss {reconstruction_loss.item()}"
                )
        print("==================== After adaround ====================")
        self._compute_and_display_local_losses(ada_quantizer, q_module, inp[0], out[0])

        ada_quantizer.use_soft_rounding = True
        ada_quantizer.V.requires_grad = False
        ada_quantizer = ada_quantizer.eval()
        q_weight = ada_quantizer(q_module.weight)
        # At the end of optimization, we need to copy the adarounded weight back to the original module
        q_module.weight.data.copy_(q_weight)  # type: ignore[operator]
        # Eager mode requires observer to be set as "weight_fake_quant" to be parsed
        q_module.weight_fake_quant = ada_quantizer.activation_post_process