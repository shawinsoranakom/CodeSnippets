def __cuda_array_interface__(self):
        """Array view description for cuda tensors.

        See:
        https://numba.pydata.org/numba-doc/dev/cuda/cuda_array_interface.html
        """
        if has_torch_function_unary(self):
            # TODO mypy doesn't support @property, see: https://github.com/python/mypy/issues/6185
            return handle_torch_function(  # pyrefly: ignore [bad-argument-count]
                Tensor.__cuda_array_interface__.__get__,  # type: ignore[attr-defined]
                (self,),
                self,  # pyrefly: ignore [bad-argument-type]
            )

        # raise AttributeError for unsupported tensors, so that
        # hasattr(cpu_tensor, "__cuda_array_interface__") is False.
        if not self.is_cuda:
            raise AttributeError(
                f"Can't get __cuda_array_interface__ on non-CUDA tensor type: {self.type()} "
                "If CUDA data is required use tensor.cuda() to copy tensor to device memory."
            )

        if self.is_sparse:
            raise AttributeError(
                f"Can't get __cuda_array_interface__ on sparse type: {self.type()} "
                "Use Tensor.to_dense() to convert to a dense tensor first."
            )

        # RuntimeError, matching tensor.__array__() behavior.
        if self.requires_grad:
            raise RuntimeError(
                "Can't get __cuda_array_interface__ on Variable that requires grad. "
                "If gradients aren't required, use var.detach() to get Variable that doesn't require grad."
            )

        typestr = _dtype_to_typestr(self.dtype)
        itemsize = self.element_size()
        shape = tuple(self.shape)
        if self.is_contiguous():
            # __cuda_array_interface__ v2 requires the strides to be omitted
            # (either not set or set to None) for C-contiguous arrays.
            strides = None
        else:
            strides = tuple(s * itemsize for s in self.stride())
        data_ptr = self.data_ptr() if self.numel() > 0 else 0
        data = (data_ptr, False)  # read-only is false

        return dict(typestr=typestr, shape=shape, strides=strides, data=data, version=2)