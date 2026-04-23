def compute_lens_change(
        self, feature_lens: int | torch.Tensor
    ) -> int | torch.Tensor:
        """feature_lens: int
        return updated feature lens.

        This used to return a different lambda function for each case that
        computed the right thing.  That does not work within Torchscript.
        If you really need this to be faster, create nn.Module()-s for all
        the cases and return one of them.  Torchscript does support that.
        """
        if self.input_layer == "nemo_conv":
            # Handle the special causal case
            subsampling_causal_cond = self.nemo_conv_settings.get(
                "subsampling", "dw_striding"
            ) in [
                "dw_striding",
                "striding",
                "striding_conv1d",
            ]
            is_causal = self.nemo_conv_settings.get("is_causal", False)
            if is_causal and subsampling_causal_cond:
                lens_change = (
                    torch.ceil(feature_lens / self.time_reduction).long()
                    if isinstance(feature_lens, Tensor)
                    else math.ceil(feature_lens / self.time_reduction)
                )
                feature_lens_remainder = feature_lens % self.time_reduction
                if isinstance(feature_lens, Tensor):
                    lens_change[feature_lens_remainder != 1] += 1
                elif feature_lens_remainder != 1:
                    lens_change += 1
                return lens_change
            ceil_func = math.ceil if isinstance(feature_lens, int) else torch.ceil
            return ceil_func(feature_lens / self.time_reduction)