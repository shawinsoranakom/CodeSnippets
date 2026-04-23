def _init_weight_qparams_dict(self, weight_qparams_dict, device):
        if weight_qparams_dict is None:
            raise AssertionError("weight_qparams_dict must not be None")
        self.is_decomposed = weight_qparams_dict["is_decomposed"]
        for key, weight_qparams in weight_qparams_dict.items():
            if key == "is_decomposed":
                continue
            # TODO: refactor the duplicated code to utils.py
            weight_qscheme = weight_qparams["qscheme"]
            weight_dtype = weight_qparams["dtype"]
            setattr(self, key + "_qscheme", weight_qscheme)
            setattr(self, key + "_dtype", weight_dtype)
            if weight_qscheme not in [
                None,
                torch.per_tensor_affine,
                torch.per_channel_affine,
            ]:
                raise AssertionError(
                    f"qscheme: {weight_qscheme} is not supported in {self._get_name()}"
                )
            if weight_qscheme is not None:
                scale = weight_qparams["scale"]
                scale_tensor = (
                    scale.detach().clone()
                    if isinstance(scale, torch.Tensor)
                    else torch.tensor(scale, dtype=torch.float, device=device)
                )
                self.register_buffer(key + "_scale", scale_tensor)
                zp = weight_qparams["zero_point"]
                zp_tensor = (
                    zp.detach().clone()
                    if isinstance(zp, torch.Tensor)
                    else torch.tensor(zp, dtype=torch.int, device=device)
                )
                self.register_buffer(key + "_zero_point", zp_tensor)
                if weight_qscheme == torch.per_channel_affine:
                    axis = weight_qparams["axis"]
                    axis_tensor = (
                        axis.detach().clone()
                        if isinstance(axis, torch.Tensor)
                        else torch.tensor(axis, dtype=torch.int, device=device)
                    )
                    self.register_buffer(key + "_axis", axis_tensor)
                else:
                    # added for TorchScriptability, not used
                    self.register_buffer(
                        key + "_axis", torch.tensor(0, dtype=torch.int, device=device)
                    )
                setattr(self, key + "_axis_int", getattr(self, key + "_axis").item())