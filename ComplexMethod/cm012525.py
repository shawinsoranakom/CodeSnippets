def reduction(
        self,
        dtype: torch.dtype,
        src_dtype: torch.dtype,
        reduction_type: ReductionType,
        value: CSEVariable | tuple[CSEVariable, ...],
    ) -> CSEVariable | tuple[CSEVariable, ...]:  # type: ignore[override]
        """
        Generate code for reduction operations in JAX/Pallas.

        Reductions in Pallas work by:
        1. Loading the input data into the kernel
        2. Applying JAX reduction operations (jnp.sum, jnp.max, etc.)
        3. Storing the reduced result

        The reduction happens over the loaded block of data.
        """
        assert self.inside_reduction

        # Handle welford_reduce using the fallback (computes via sum reductions)
        if reduction_type == "welford_reduce":
            return self.welford_reduce_fallback(dtype, value)

        if isinstance(value, tuple):
            raise Unsupported(
                "Tuple reductions (e.g., welford_combine) not supported in Pallas backend"
            )

        # Check if this reduction is already cached.
        cache_key = (src_dtype, reduction_type, value)
        if cache_key in self.cse.reduction_cache:
            return self.cse.reduction_cache[cache_key]

        # Map reduction types to JAX functions
        reduction_ops = {
            "sum": "jnp.sum",
            "prod": "jnp.prod",  # CPU only - not supported in Pallas GPU (Mosaic) backend
            "max": "jnp.max",
            "min": "jnp.min",
            "any": "jnp.any",
            "argmax": "jnp.argmax",
            "argmin": "jnp.argmin",
        }

        # Determine if this is a partial reduction (has pointwise dimensions)
        # or a full reduction to scalar
        pointwise_prefixes = OrderedSet(["x", "y", "z"])
        has_pointwise = any(p in self.numels for p in pointwise_prefixes)
        pointwise_numel: int | None = self._compute_prefix_numel(pointwise_prefixes)
        reduction_numel: int | None = self._compute_reduction_numel()
        n_reduction_dims = sum(
            1 for var, entry in self.range_tree_nodes.items() if entry.is_reduction
        )

        is_partial_reduction = (
            has_pointwise
            and pointwise_numel is not None
            and pointwise_numel > 1
            and reduction_numel
            and n_reduction_dims > 0
        )
        is_symbolic_partial = (
            has_pointwise and n_reduction_dims > 0 and pointwise_numel is None
        )

        if reduction_type == "xor_sum":
            if is_partial_reduction:
                axes = self._get_reduction_axes()
                axis_expr = axes[0] if len(axes) == 1 else axes
                reduction_expr = f"jnp.bitwise_xor.reduce({value}, axis={axis_expr})"
            else:
                reduction_expr = f"jnp.bitwise_xor.reduce({value})"
        elif reduction_type in ("argmax", "argmin"):
            reduction_op = reduction_ops[reduction_type]
            if is_partial_reduction:
                # argmax/argmin only accept a single axis
                axes = self._get_reduction_axes()
                reduction_expr = f"{reduction_op}({value}, axis={axes[-1]})"
            else:
                reduction_expr = f"{reduction_op}({value})"
        elif reduction_type in reduction_ops:
            reduction_op = reduction_ops[reduction_type]
            if is_partial_reduction:
                axes = self._get_reduction_axes()
                axis_expr = axes[0] if len(axes) == 1 else axes
                reduction_expr = (
                    f"{reduction_op}({value}, axis={axis_expr}, keepdims=True)"
                )
            elif is_symbolic_partial:
                # With symbolic shapes, strided loads produce a degenerate
                # batch dim at axis=0 that just needs squeezing.
                reduction_expr = f"{reduction_op}({value}, axis=0)"
            else:
                reduction_expr = f"{reduction_op}({value})"
        else:
            raise Unsupported(
                f"Reduction type '{reduction_type}' not yet supported in Pallas backend. "
                f"Supported types: {list(reduction_ops.keys())}, xor_sum"
            )

        # Generate CSE variable for the reduction result
        result = self.cse.generate(
            self.compute,
            reduction_expr,
            dtype=dtype,
        )

        # Cache the result
        self.cse.reduction_cache[cache_key] = result
        return result