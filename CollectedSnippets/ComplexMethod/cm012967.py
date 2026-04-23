def _init_weight_qparams(self, weight_qparams, device):
        if weight_qparams is None:
            weight_qparams = {
                "qscheme": torch.per_tensor_affine,
                "dtype": torch.quint8,
                "scale": 1.0,
                "zero_point": 0,
            }

        self.weight_qscheme: torch.qscheme = weight_qparams["qscheme"]
        self.weight_dtype = weight_qparams["dtype"]
        if self.weight_qscheme not in [
            None,
            torch.per_tensor_affine,
            torch.per_channel_affine,
            torch.per_channel_affine_float_qparams,
        ]:
            raise AssertionError(
                f"qscheme: {self.weight_qscheme} is not supported in reference quantized {self._get_name()}"
            )
        if self.weight_dtype in [
            torch.quint8,
            torch.qint8,
            torch.quint4x2,
            torch.qint32,
        ]:
            zero_point_dtype = (
                weight_qparams["zero_point"].dtype
                if isinstance(weight_qparams["zero_point"], torch.Tensor)
                else torch.int
            )
            w_scale = weight_qparams["scale"]
            w_scale_tensor = (
                w_scale.detach().clone()
                if isinstance(w_scale, torch.Tensor)
                else torch.tensor(w_scale, dtype=torch.float, device=device)
            )
            self.register_buffer("weight_scale", w_scale_tensor)
            w_zp = weight_qparams["zero_point"]
            w_zp_tensor = (
                w_zp.detach().clone()
                if isinstance(w_zp, torch.Tensor)
                else torch.tensor(w_zp, dtype=zero_point_dtype, device=device)
            )
            self.register_buffer("weight_zero_point", w_zp_tensor)
            if self.weight_qscheme in [
                torch.per_channel_affine,
                torch.per_channel_affine_float_qparams,
            ]:
                w_axis = weight_qparams["axis"]
                w_axis_tensor = (
                    w_axis.detach().clone()
                    if isinstance(w_axis, torch.Tensor)
                    else torch.tensor(w_axis, dtype=torch.int, device=device)
                )
                self.register_buffer("weight_axis", w_axis_tensor)
            else:
                # added for TorchScriptability, not used
                self.register_buffer(
                    "weight_axis", torch.tensor(0, dtype=torch.int, device=device)
                )
        else:
            # added for TorchScriptability, and for torch.float
            self.register_buffer(
                "weight_scale", torch.tensor(1.0, dtype=torch.float, device=device)
            )
            self.register_buffer(
                "weight_zero_point", torch.tensor(0, dtype=torch.int, device=device)
            )
            self.register_buffer(
                "weight_axis", torch.tensor(0, dtype=torch.int, device=device)
            )

        self.is_decomposed: bool = weight_qparams.get("is_decomposed", False)
        # store weight_axis as weight_axis_int due to some constraints of torchdynamo.export
        # for capturing `.item` operations
        self.weight_axis_int: int = self.weight_axis.item()  # type: ignore[operator, assignment]

        self.weight_quant_min: int | None = weight_qparams.get("quant_min")

        self.weight_quant_max: int | None = weight_qparams.get("quant_max")