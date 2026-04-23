def network_apply_weights(self: Union[torch.nn.Conv2d, torch.nn.Linear, torch.nn.GroupNorm, torch.nn.LayerNorm, torch.nn.MultiheadAttention]):
    """
    Applies the currently selected set of networks to the weights of torch layer self.
    If weights already have this particular set of networks applied, does nothing.
    If not, restores original weights from backup and alters weights according to networks.
    """

    network_layer_name = getattr(self, 'network_layer_name', None)
    if network_layer_name is None:
        return

    current_names = getattr(self, "network_current_names", ())
    wanted_names = tuple((x.name, x.te_multiplier, x.unet_multiplier, x.dyn_dim) for x in loaded_networks)

    weights_backup = getattr(self, "network_weights_backup", None)
    if weights_backup is None and wanted_names != ():
        if current_names != () and not allowed_layer_without_weight(self):
            raise RuntimeError(f"{network_layer_name} - no backup weights found and current weights are not unchanged")

        if isinstance(self, torch.nn.MultiheadAttention):
            weights_backup = (store_weights_backup(self.in_proj_weight), store_weights_backup(self.out_proj.weight))
        else:
            weights_backup = store_weights_backup(self.weight)

        self.network_weights_backup = weights_backup

    bias_backup = getattr(self, "network_bias_backup", None)
    if bias_backup is None and wanted_names != ():
        if isinstance(self, torch.nn.MultiheadAttention) and self.out_proj.bias is not None:
            bias_backup = store_weights_backup(self.out_proj.bias)
        elif getattr(self, 'bias', None) is not None:
            bias_backup = store_weights_backup(self.bias)
        else:
            bias_backup = None

        # Unlike weight which always has value, some modules don't have bias.
        # Only report if bias is not None and current bias are not unchanged.
        if bias_backup is not None and current_names != ():
            raise RuntimeError("no backup bias found and current bias are not unchanged")

        self.network_bias_backup = bias_backup

    if current_names != wanted_names:
        network_restore_weights_from_backup(self)

        for net in loaded_networks:
            module = net.modules.get(network_layer_name, None)
            if module is not None and hasattr(self, 'weight') and not isinstance(module, modules.models.sd3.mmdit.QkvLinear):
                try:
                    with torch.no_grad():
                        if getattr(self, 'fp16_weight', None) is None:
                            weight = self.weight
                            bias = self.bias
                        else:
                            weight = self.fp16_weight.clone().to(self.weight.device)
                            bias = getattr(self, 'fp16_bias', None)
                            if bias is not None:
                                bias = bias.clone().to(self.bias.device)
                        updown, ex_bias = module.calc_updown(weight)

                        if len(weight.shape) == 4 and weight.shape[1] == 9:
                            # inpainting model. zero pad updown to make channel[1]  4 to 9
                            updown = torch.nn.functional.pad(updown, (0, 0, 0, 0, 0, 5))

                        self.weight.copy_((weight.to(dtype=updown.dtype) + updown).to(dtype=self.weight.dtype))
                        if ex_bias is not None and hasattr(self, 'bias'):
                            if self.bias is None:
                                self.bias = torch.nn.Parameter(ex_bias).to(self.weight.dtype)
                            else:
                                self.bias.copy_((bias + ex_bias).to(dtype=self.bias.dtype))
                except RuntimeError as e:
                    logging.debug(f"Network {net.name} layer {network_layer_name}: {e}")
                    extra_network_lora.errors[net.name] = extra_network_lora.errors.get(net.name, 0) + 1

                continue

            module_q = net.modules.get(network_layer_name + "_q_proj", None)
            module_k = net.modules.get(network_layer_name + "_k_proj", None)
            module_v = net.modules.get(network_layer_name + "_v_proj", None)
            module_out = net.modules.get(network_layer_name + "_out_proj", None)

            if isinstance(self, torch.nn.MultiheadAttention) and module_q and module_k and module_v and module_out:
                try:
                    with torch.no_grad():
                        # Send "real" orig_weight into MHA's lora module
                        qw, kw, vw = self.in_proj_weight.chunk(3, 0)
                        updown_q, _ = module_q.calc_updown(qw)
                        updown_k, _ = module_k.calc_updown(kw)
                        updown_v, _ = module_v.calc_updown(vw)
                        del qw, kw, vw
                        updown_qkv = torch.vstack([updown_q, updown_k, updown_v])
                        updown_out, ex_bias = module_out.calc_updown(self.out_proj.weight)

                        self.in_proj_weight += updown_qkv
                        self.out_proj.weight += updown_out
                    if ex_bias is not None:
                        if self.out_proj.bias is None:
                            self.out_proj.bias = torch.nn.Parameter(ex_bias)
                        else:
                            self.out_proj.bias += ex_bias

                except RuntimeError as e:
                    logging.debug(f"Network {net.name} layer {network_layer_name}: {e}")
                    extra_network_lora.errors[net.name] = extra_network_lora.errors.get(net.name, 0) + 1

                continue

            if isinstance(self, modules.models.sd3.mmdit.QkvLinear) and module_q and module_k and module_v:
                try:
                    with torch.no_grad():
                        # Send "real" orig_weight into MHA's lora module
                        qw, kw, vw = self.weight.chunk(3, 0)
                        updown_q, _ = module_q.calc_updown(qw)
                        updown_k, _ = module_k.calc_updown(kw)
                        updown_v, _ = module_v.calc_updown(vw)
                        del qw, kw, vw
                        updown_qkv = torch.vstack([updown_q, updown_k, updown_v])
                        self.weight += updown_qkv

                except RuntimeError as e:
                    logging.debug(f"Network {net.name} layer {network_layer_name}: {e}")
                    extra_network_lora.errors[net.name] = extra_network_lora.errors.get(net.name, 0) + 1

                continue

            if module is None:
                continue

            logging.debug(f"Network {net.name} layer {network_layer_name}: couldn't find supported operation")
            extra_network_lora.errors[net.name] = extra_network_lora.errors.get(net.name, 0) + 1

        self.network_current_names = wanted_names