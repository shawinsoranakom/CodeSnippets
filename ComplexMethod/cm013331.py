def __post_init__(self):
        self._original_opinfo_args = asdict(self).copy()

        if self.dtypes is None:
            raise AssertionError(f"OpInfo for {self.name} has no dtypes!")

        # Validates the dtypes are generated from the dispatch-related functions
        for name, val in self.dtypesIf.items():
            if val is not None:
                if not isinstance(val, _dispatch_dtypes):
                    raise AssertionError(f"Expected _dispatch_dtypes, got {type(val)}")
                self.dtypesIf[name] = set(val)

        if self.aten_name is None:
            self.aten_name = self.name

        # Attribute to verify dynamic_dtypes are used.
        self.dynamic_dtypes = any(
            isinstance(dtypes, utils._dynamic_dispatch_dtypes)
            for dtypes in self.dtypesIf.values()
        )

        if self.dynamic_dtypes:
            # Make sure `dtyesIfCUDA` is dynamic, if dynamic dispatch is used for CPU
            # This is because, below we set dtypesIfCUDA to dtypes if they are None.
            if not isinstance(self.dtypesIfCUDA, utils._dynamic_dispatch_dtypes):
                raise AssertionError(
                    f"To use dynamic dtypes for operator {self.name}, "
                    "acquire the dtypes dynamically for argument `dtypesIfCUDA`. "
                    "This is to ensure that CUDA dtypes are acquired correctly as they "
                    "differ from CPU dtypes occasionally"
                )
            if not isinstance(self.dtypesIfMPS, utils._dynamic_dispatch_dtypes):
                raise AssertionError(
                    f"To use dynamic dtypes for operator {self.name}, "
                    "acquire the dtypes dynamically for argument `dtypesIfMPS`. "
                    "This is to ensure that MPS dtypes are acquired correctly as they "
                    "differ from CPU dtypes occasionally"
                )

        self.dtypes = set(self.dtypes)

        # NOTE: backward dtypes must be acquired before forward dtypes
        #   since they fallback to explicit (not implicit!) specifications of
        #   forward dtypes
        self.backward_dtypesIfROCM = (
            set(self.backward_dtypesIfROCM)
            if self.backward_dtypesIfROCM is not None
            else (
                self.backward_dtypesIfCUDA
                if self.backward_dtypesIfCUDA is not None
                else self.backward_dtypes
                if self.backward_dtypes is not None
                else self.dtypesIfROCM
                if self.dtypesIfROCM is not None
                else self.dtypesIfCUDA
                if self.dtypesIfCUDA is not None
                else self.dtypes
            )
        )
        self.backward_dtypesIfCUDA = (
            set(self.backward_dtypesIfCUDA)
            if self.backward_dtypesIfCUDA is not None
            else (
                self.backward_dtypes
                if self.backward_dtypes is not None
                else self.dtypesIfCUDA
                if self.dtypesIfCUDA is not None
                else self.dtypes
            )
        )
        self.backward_dtypesIfMPS = (
            set(self.backward_dtypesIfMPS) - {torch.float64, torch.cdouble}
            if self.backward_dtypesIfMPS is not None
            else (
                set(self.backward_dtypes) - {torch.float64, torch.cdouble}
                if self.backward_dtypes is not None
                else set(self.dtypesIfMPS) - {torch.float64, torch.cdouble}
                if self.dtypesIfMPS is not None
                else set(self.dtypes) - {torch.float64, torch.cdouble}
            )
        )
        self.backward_dtypesIfHpu = (
            set(self.backward_dtypesIfHpu)
            if self.backward_dtypesIfHpu is not None
            else (
                self.backward_dtypes
                if self.backward_dtypes is not None
                else self.dtypes
            )
        )

        self.backward_dtypes = (
            set(self.backward_dtypes)
            if self.backward_dtypes is not None
            else self.dtypes
        )

        # Inherit from cpu
        for dev_type in ["cuda", "hpu"]:
            if self.dtypesIf.get(dev_type) is None:
                self.dtypesIf[dev_type] = self.dtypes

        # Inherit from CUDA
        for dev_type in ["rocm", "xpu"]:
            if self.dtypesIf.get(dev_type) is None:
                self.dtypesIf[dev_type] = self.dtypesIf["cuda"]

        # Inherit from cpu
        for dev_type in ["mps"]:
            if self.dtypesIf.get(dev_type) is None:
                # Double floats are not supported on MPS
                self.dtypesIf[dev_type] = self.dtypes - {torch.float64, torch.cdouble}
            else:
                self.dtypesIf[dev_type] = self.dtypesIf[dev_type] - {
                    torch.float64,
                    torch.cdouble,
                }

        # NOTE: if the op is unspecified it is assumed to be under the torch namespace
        if not self.op:
            self.op = _getattr_qual(torch, self.name)

        if self.method_variant is _NOTHING:
            self.method_variant = getattr(torch.Tensor, self.name, None)

        # attributes like real, imag are not callable
        if not callable(self.method_variant):
            self.method_variant = None

        if self.inplace_variant is _NOTHING:
            inplace_name = self.name + "_"
            self.inplace_variant = getattr(torch.Tensor, inplace_name, None)

        if self.operator_variant is _NOTHING:
            self.operator_variant = getattr(operator, self.name, None)

        if self.inplace_operator_variant is _NOTHING:
            # Note: operator.i<op> will use operator.<op> and assign the result to the lhs when no
            # __i<op>__ method is found. This results in the appearance of an inplace operator variant which
            # does not have the correct inplace behavior. To avoid this, we guard automatic detection of the inplace
            # operator with a check that an inplace variant exists.
            if self.inplace_variant is not None:
                inplace_operator_name = "i" + self.name
                self.inplace_operator_variant = getattr(
                    operator, inplace_operator_name, None
                )
            else:
                self.inplace_operator_variant = None

        self.decorators = (*self.decorators, *self.skips)

        # Specifying sample inputs function without specifying the
        # corresponding layout support implies the layout support:
        if self.supports_sparse is None:
            self.supports_sparse = self.sample_inputs_sparse_coo_func is not None
        if self.sample_inputs_sparse_coo_func is None:
            self.sample_inputs_sparse_coo_func = self._sample_inputs_unspecified

        if self.supports_sparse_csr is None:
            self.supports_sparse_csr = self.sample_inputs_sparse_csr_func is not None
        if self.sample_inputs_sparse_csr_func is None:
            self.sample_inputs_sparse_csr_func = self._sample_inputs_unspecified

        if self.supports_sparse_csc is None:
            self.supports_sparse_csc = self.sample_inputs_sparse_csc_func is not None
        if self.sample_inputs_sparse_csc_func is None:
            self.sample_inputs_sparse_csc_func = self._sample_inputs_unspecified

        if self.supports_sparse_bsr is None:
            self.supports_sparse_bsr = self.sample_inputs_sparse_bsr_func is not None
        if self.sample_inputs_sparse_bsr_func is None:
            self.sample_inputs_sparse_bsr_func = self._sample_inputs_unspecified

        if self.supports_sparse_bsc is None:
            self.supports_sparse_bsc = self.sample_inputs_sparse_bsc_func is not None
        if self.sample_inputs_sparse_bsc_func is None:
            self.sample_inputs_sparse_bsc_func = self._sample_inputs_unspecified

        if self.supports_njt is None:
            self.supports_njt = False

        # We run the sampling functions without tracking the gradiends of the creation of inputs
        self.sample_inputs_func = torch.no_grad()(self.sample_inputs_func)
        self.sample_inputs_sparse_coo_func = torch.no_grad()(
            self.sample_inputs_sparse_coo_func
        )
        self.sample_inputs_sparse_csr_func = torch.no_grad()(
            self.sample_inputs_sparse_csr_func
        )
        self.sample_inputs_sparse_csc_func = torch.no_grad()(
            self.sample_inputs_sparse_csc_func
        )
        self.sample_inputs_sparse_bsr_func = torch.no_grad()(
            self.sample_inputs_sparse_bsr_func
        )
        self.sample_inputs_sparse_bsc_func = torch.no_grad()(
            self.sample_inputs_sparse_bsc_func
        )
        if self.reference_inputs_func is not None:
            self.reference_inputs_func = torch.no_grad()(self.reference_inputs_func)

        if not self.autodiff_fusible_nodes:
            self.autodiff_fusible_nodes = []

        if self.autodiff_nonfusible_nodes is None:
            self.autodiff_nonfusible_nodes = ["aten::" + self.name]

        # Autograd support

        # Autograd flags that depend on backward AD only
        # - If setting has been explicitly set, raise error if inconsistent
        if self.supports_gradgrad is None:
            self.supports_gradgrad = self.supports_autograd
        else:
            if self.supports_gradgrad and not self.supports_autograd:
                raise AssertionError(
                    "supports_gradgrad refines the part of autograd is supported, so it should "
                    "not be set if supports_autograd is False"
                )
        if self.check_batched_grad is None:
            self.check_batched_grad = self.supports_autograd or self.supports_forward_ad
        else:
            if self.check_batched_grad and not (
                self.supports_autograd or self.supports_forward_ad
            ):
                raise AssertionError(
                    "check_batched_grad refines the part of autograd that will be checked (by gradcheck), so "
                    "it should not be set if supports_autograd is False"
                )
        if self.check_batched_gradgrad is None:
            self.check_batched_gradgrad = self.supports_gradgrad
        else:
            if self.check_batched_gradgrad and not self.supports_gradgrad:
                raise AssertionError(
                    "check_batched_gradgrad refines the part of autograd that will be checked (by "
                    "gradgradcheck), so it should not be set if either supports_gradgrad or supports_autograd "
                    "is False."
                )
        if self.check_batched_forward_grad is None:
            self.check_batched_forward_grad = self.supports_forward_ad
        else:
            if self.check_batched_forward_grad and not self.supports_forward_ad:
                raise AssertionError(
                    "check_batched_forward_grad should only be used when supports_forward_ad "
                    "is True. It is used to disable the test in the specific cases "
                    "where the op supports forward ad but fails to compute "
                    "batched forward grad."
                )

        if self.check_inplace_batched_forward_grad is None:
            self.check_inplace_batched_forward_grad = self.check_batched_forward_grad
        else:
            if (
                self.check_inplace_batched_forward_grad
                and not self.check_batched_forward_grad
            ):
                raise AssertionError(
                    "check_batched_forward_grad should only be used when check_batched_forward_grad "
                    "is True. It is used to disable the test in the specific cases "
                    "where the op supports batched forward grad but fails to compute batched forward "
                    "grad for the inplace variant of the op."
                )

        if self.supports_fwgrad_bwgrad and not self.supports_autograd:
            raise AssertionError(
                "supports_fwgrad_bwgrad enables forward-over-backward gradgrad checks and should only be "
                f"True if backward ad is also checked, i.e., supports_forward_ad should be True. ({self.name})"
            )

        # Autograd flags that depend on both forward AD and backward AD
        if self.supports_inplace_autograd is None:
            self.supports_inplace_autograd = (
                self.supports_autograd or self.supports_forward_ad
            )
        else:
            if (
                self.supports_inplace_autograd
                and not self.supports_autograd
                and not self.supports_forward_ad
            ):
                raise AssertionError(
                    "supports_inplace_autograd refines the part of autograd that is supported, so "
                    "it should not be set if both supports_autograd and supports_forward_ad are False"
                )

        if self.aliases is not None:
            self.aliases = tuple(AliasInfo(a) for a in self.aliases)  # type: ignore[assignment]
        else:
            self.aliases = ()