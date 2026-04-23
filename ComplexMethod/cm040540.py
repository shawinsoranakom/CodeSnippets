def __call__(self, *args, **kwargs):
        if traceback_utils.is_traceback_filtering_enabled():
            # Wrap self.call to provide helpful info in case of exception
            if any_symbolic_tensors(args, kwargs):
                call_fn = self.symbolic_call
            else:
                if getattr(self, "_remat_mode", None) is not None:
                    if getattr(self, "quantization_mode", None) is not None:
                        call_fn = self.rematerialized_call(
                            self.quantized_call,
                            *args,
                            **kwargs,
                        )
                    else:
                        call_fn = self.rematerialized_call(
                            self.call, *args, **kwargs
                        )
                else:
                    if getattr(self, "quantization_mode", None) is not None:
                        call_fn = self.quantized_call
                    else:
                        call_fn = self.call
            call_fn = traceback_utils.inject_argument_info_in_traceback(
                call_fn,
                object_name=(f"{self.__class__.__name__}.call()"),
            )
            return call_fn(*args, **kwargs)

        # Plain flow.
        if any_symbolic_tensors(args, kwargs):
            return self.symbolic_call(*args, **kwargs)
        elif getattr(self, "_remat_mode", None) is not None:
            if getattr(self, "quantization_mode", None) is not None:
                return self.rematerialized_call(
                    self.quantized_call, *args, **kwargs
                )(*args, **kwargs)
            else:
                return self.rematerialized_call(self.call, *args, **kwargs)(
                    *args, **kwargs
                )
        else:
            if getattr(self, "quantization_mode", None) is not None:
                return self.quantized_call(*args, **kwargs)
            else:
                return self.call(*args, **kwargs)