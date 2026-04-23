def to(self, *args, **kwargs):
        # For BNB/GPTQ models, we prevent users from casting the model to another dtype to restrict unwanted behaviours.
        # the correct API should be to load the model with the desired dtype directly through `from_pretrained`.
        dtype_present_in_args = "dtype" in kwargs

        if not dtype_present_in_args:
            for arg in args:
                if isinstance(arg, torch.dtype):
                    dtype_present_in_args = True
                    break

        if getattr(self, "quantization_method", None) == QuantizationMethod.HQQ:
            from hqq.core.quantize import HQQLinear

            # Since HQQLinear stores some tensors in the 'meta' attribute, we must
            # explicitly move the parameters to the target device for each HQQLinear layer after `to`.
            super().to(*args, **kwargs)
            for module in self.modules():
                if isinstance(module, HQQLinear):
                    if "device" in kwargs:
                        device = kwargs["device"]
                    else:
                        device = args[0]
                    if "dtype" in kwargs:
                        dtype = kwargs["dtype"]
                    elif dtype_present_in_args:
                        dtype = arg
                    else:
                        dtype = None
                    # Due to the current messy implementation of HQQLinear, updating `compute_dtype`
                    # followed by calling the `cuda` method achieves the intended behavior of `to`,
                    # even when the target device is CPU.
                    if dtype is not None:
                        module.compute_dtype = dtype
                    module.cuda(device)
            return self

        if dtype_present_in_args and getattr(self, "quantization_method", None) == QuantizationMethod.QUARK:
            raise ValueError("Casting a Quark quantized model to a new `dtype` is not supported.")

        # Checks if the model has been loaded in 4-bit or 8-bit with BNB
        if getattr(self, "quantization_method", None) == QuantizationMethod.BITS_AND_BYTES:
            if dtype_present_in_args:
                raise ValueError(
                    "You cannot cast a bitsandbytes model in a new `dtype`. Make sure to load the model using `from_pretrained` using the"
                    " desired `dtype` by passing the correct `dtype` argument."
                )

            if getattr(self, "is_loaded_in_8bit", False) and not is_bitsandbytes_available("0.48"):
                raise ValueError(
                    "You need to install `pip install bitsandbytes>=0.48.0` if you want to move a 8-bit model across devices using to()."
                )
        elif getattr(self, "quantization_method", None) == QuantizationMethod.GPTQ:
            if dtype_present_in_args:
                raise ValueError(
                    "You cannot cast a GPTQ model in a new `dtype`. Make sure to load the model using `from_pretrained` using the desired"
                    " `dtype` by passing the correct `dtype` argument."
                )
        return super().to(*args, **kwargs)