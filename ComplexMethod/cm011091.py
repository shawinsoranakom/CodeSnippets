def _init_metadata(
        cls,
        self,
        param_infos: list[ParamInfo],
        numels: list[int],
        shapes: list[torch.Size],
        strides: list[tuple[int, ...]],
        contiguities: list[bool],
        fqns: list[str],
        shared_param_infos: list[SharedParamInfo],
        param_extensions: list[Any | None],
        params: list[nn.Parameter] | None,
        shared_params: list[nn.Parameter] | None,
        is_padding_mask: list[bool],
    ) -> None:
        """
        Initialize attributes holding metadata about the original parameters comprising the flat parameter.

        We expose this method separate from the constructor to keep the
        constructor only responsible for the flat parameter's tensor data. This
        method should only be called once per model, while the constructor may
        be called multiple times, e.g. when reloading from a checkpoint, in
        which case only the tensor data needs to be passed to the constructor.
        Since :meth:`load_state_dict` is implemented via :meth:`copy_`, the
        metadata is correctly assumed to be unchanged.

        Args:
            See the Attributes in the class docstring.
        """
        if len(param_infos) != len(shapes):
            raise AssertionError(
                f"Expected param_infos length {len(param_infos)} to match shapes length {len(shapes)}"
            )
        if len(param_infos) != len(strides):
            raise AssertionError(
                f"Expected param_infos length {len(param_infos)} to match strides length {len(strides)}"
            )
        if len(param_infos) != len(contiguities):
            raise AssertionError(
                f"Expected param_infos length {len(param_infos)} to match contiguities length {len(contiguities)}"
            )
        if len(param_infos) != len(fqns):
            raise AssertionError(
                f"Expected param_infos length {len(param_infos)} to match fqns length {len(fqns)}"
            )
        if len(param_infos) != len(param_extensions):
            raise AssertionError(
                f"Expected param_infos length {len(param_infos)} to match param_extensions length {len(param_extensions)}"
            )
        self._num_params = len(param_infos)
        self._param_infos = param_infos
        self._shapes = shapes
        self._strides = strides
        self._contiguities = contiguities
        self._fqns = fqns
        self._param_extensions = param_extensions
        self._is_padding_mask = is_padding_mask

        numels_without_padding: list[int] = []
        for numel, is_padding in zip(numels, is_padding_mask):
            if not is_padding:
                numels_without_padding.append(numel)
        self._numels = tuple(numels_without_padding)
        self._numels_with_padding = tuple(numels)
        if len(self._numels) != self._num_params:
            raise AssertionError(
                f"Expected _numels length {len(self._numels)} to equal _num_params {self._num_params}"
            )

        self._shared_param_infos = tuple(shared_param_infos)
        self._modules = {pi.module for pi in self._param_infos}.union(
            {spi.module for spi in self._shared_param_infos}
        )
        if (params is None) != (shared_params is None):
            raise AssertionError(
                "Expected params and shared_params to both be None or both be not None"
            )
        if params is not None:
            if shared_params is None or len(shared_params) != len(shared_param_infos):
                raise AssertionError(
                    f"Expected shared_params to be not None and have length {len(shared_param_infos)}, got {shared_params}"
                )
            self._params = []
            for param, is_padding in zip(params, is_padding_mask):
                if not is_padding:
                    self._params.append(param)
            if shared_params is not None:
                self._shared_params = shared_params
            else:
                self._shared_params = []
            # Mark the original parameters to avoid flattening them into
            # another `FlatParameter` during recursive construction
            for param in chain(self._params, self._shared_params):
                _set_fsdp_flattened(param)
            self._is_grad_none_mask = [False for _ in range(self._num_params)]
            self._tensors = [None for _ in range(self._num_params)]
        else:
            self._params = None
            self._shared_params = None
            self._is_grad_none_mask = None
            self._tensors = None
        self._unpadded_unsharded_size = self.size()
        _set_fsdp_flattened(self)
        # Tracks whether the `FlatParameter`'s post-backward hook has been
        # called to modify the behavior of the post-backward callback
        self._post_backward_called = False