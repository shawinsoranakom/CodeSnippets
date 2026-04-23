def post_init(self):
        r"""
        Safety checker that arguments are correct - also replaces some NoneType arguments with their default values.
        """

        if self.hadamard_group_size is None:
            if self.forward_dtype == "nvfp4":
                self.hadamard_group_size = 16
            else:
                self.hadamard_group_size = 32

        if self.forward_dtype == "mxfp4":
            if self.forward_method not in ["abs_max", "quest"]:
                raise ValueError("Only 'abs_max' and 'quest' are supported for forward_method for 'mxfp4'.")
            if self.hadamard_group_size is None:
                self.hadamard_group_size = 32
            if self.hadamard_group_size not in [32, 64, 128]:
                raise ValueError("Only a `hadamard_group_size` of [32, 64, 128] is supported for 'mxfp4'.")
        elif self.forward_dtype == "nvfp4":
            if self.forward_method != "abs_max":
                raise ValueError("Only 'abs_max' is supported for forward_method for 'nvfp4'.")
            if self.hadamard_group_size is None:
                self.hadamard_group_size = 16
            if self.hadamard_group_size not in [16, 32, 64, 128]:
                raise ValueError("Only a `hadamard_group_size` of [16, 32, 64, 128] is supported for 'nvfp4'.")
        else:
            raise ValueError("Only 'mxfp4' and 'nvfp4' are supported for forward_dtype for now.")

        if self.backward_dtype not in ["bf16", "mxfp8", "mxfp4"]:
            raise ValueError("Only 'bf16', 'mxfp8' and 'mxfp4' are supported for backward_dtype for now.")

        if self.backward_dtype != "bf16" and self.forward_dtype != "mxfp4":
            raise ValueError("Only 'mxfp4' forward is compatible with non-bf16 backwards for now.")

        if self.transform_init not in ["hadamard", "identity", "gsr"]:
            raise ValueError("Only 'hadamard', 'identity' and 'gsr' are supported for transform_init.")

        if self.modules_to_not_convert is None:
            self.modules_to_not_convert = ["lm_head"]