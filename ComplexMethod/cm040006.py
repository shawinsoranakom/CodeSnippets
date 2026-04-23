def quantized_call(self, *args, **kwargs):
        current_remat_mode = get_current_remat_mode()

        if (
            current_remat_mode != self._remat_mode
            and current_remat_mode is not None
        ):
            warnings.warn(
                f"The RematScope at call time ({current_remat_mode}) differs "
                f"the one set during layer initialization "
                f"({self._remat_mode}). "
                f"Restoring the correct rematerialization mode "
                f"{self._remat_mode} for this layer."
            )
        if self.quantization_mode == "int8":
            return self._int8_call(*args, **kwargs)
        elif self.quantization_mode == "float8":
            return self._float8_call(*args, **kwargs)
        elif self.quantization_mode == "int4":
            return self._int4_call(*args, **kwargs)
        elif self.quantization_mode == "gptq":
            return self._gptq_call(*args, **kwargs)
        elif self.quantization_mode == "awq":
            return self._awq_call(*args, **kwargs)
        else:
            raise self._quantization_mode_error(self.quantization_mode)