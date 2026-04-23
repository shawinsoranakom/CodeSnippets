def _op(
        self,
        at_op: _AtOp,
        in_place_op: Callable[[Array, Array | complex], Array] | None,
        out_of_place_op: Callable[[Array, Array], Array] | None,
        y: Array | complex,
        /,
        copy: bool | None,
        xp: ModuleType | None,
    ) -> Array:
        """
        Implement all update operations.

        Parameters
        ----------
        at_op : _AtOp
            Method of JAX's Array.at[].
        in_place_op : Callable[[Array, Array | complex], Array] | None
            In-place operation to apply on mutable backends::

                x[idx] = in_place_op(x[idx], y)

            If None::

                x[idx] = y

        out_of_place_op : Callable[[Array, Array], Array] | None
            Out-of-place operation to apply when idx is a boolean mask and the backend
            doesn't support in-place updates::

                x = xp.where(idx, out_of_place_op(x, y), x)

            If None::

                x = xp.where(idx, y, x)

        y : array or complex
            Right-hand side of the operation.
        copy : bool or None
            Whether to copy the input array. See the class docstring for details.
        xp : array_namespace, optional
            The array namespace for the input array. Default: infer.

        Returns
        -------
        Array
            Updated `x`.
        """
        from ._funcs import apply_where  # pylint: disable=cyclic-import

        x, idx = self._x, self._idx
        xp = array_namespace(x, y) if xp is None else xp

        if isinstance(idx, Undef):
            msg = (
                "Index has not been set.\n"
                "Usage: either\n"
                "    at(x, idx).set(value)\n"
                "or\n"
                "    at(x)[idx].set(value)\n"
                "(same for all other methods)."
            )
            raise ValueError(msg)

        if copy not in (True, False, None):
            msg = f"copy must be True, False, or None; got {copy!r}"
            raise ValueError(msg)

        writeable = None if copy else is_writeable_array(x)

        # JAX inside jax.jit doesn't support in-place updates with boolean
        # masks; Dask exclusively supports __setitem__ but not iops.
        # We can handle the common special case of 0-dimensional y
        # with where(idx, y, x) instead.
        if (
            (is_dask_array(idx) or is_jax_array(idx))
            and idx.dtype == xp.bool
            and idx.shape == x.shape
        ):
            y_xp = xp.asarray(y, dtype=x.dtype, device=_compat.device(x))
            if y_xp.ndim == 0:
                if out_of_place_op:  # add(), subtract(), ...
                    # suppress inf warnings on Dask
                    out = apply_where(
                        idx, (x, y_xp), out_of_place_op, fill_value=x, xp=xp
                    )
                    # Undo int->float promotion on JAX after _AtOp.DIVIDE
                    out = xp.astype(out, x.dtype, copy=False)
                else:  # set()
                    out = xp.where(idx, y_xp, x)

                if copy is False:
                    x[()] = out
                    return x
                return out

            # else: this will work on eager JAX and crash on jax.jit and Dask

        if copy or (copy is None and not writeable):
            if is_jax_array(x):
                # Use JAX's at[]
                func = cast(
                    Callable[[Array | complex], Array],
                    getattr(x.at[idx], at_op.value),  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue,reportUnknownArgumentType]
                )
                out = func(y)
                # Undo int->float promotion on JAX after _AtOp.DIVIDE
                return xp.astype(out, x.dtype, copy=False)

            # Emulate at[] behaviour for non-JAX arrays
            # with a copy followed by an update

            x = xp.asarray(x, copy=True)
            # A copy of a read-only numpy array is writeable
            # Note: this assumes that a copy of a writeable array is writeable
            assert not writeable
            writeable = None

        if writeable is None:
            writeable = is_writeable_array(x)
        if not writeable:
            # sparse crashes here
            msg = f"Can't update read-only array {x}"
            raise ValueError(msg)

        # Work around bug in PyTorch where __setitem__ doesn't
        # always support mismatched dtypes
        # https://github.com/pytorch/pytorch/issues/150017
        if is_torch_array(y):
            y = xp.astype(y, x.dtype, copy=False)

        # Backends without boolean indexing (other than JAX) crash here
        if in_place_op:  # add(), subtract(), ...
            x[idx] = in_place_op(x[idx], y)
        else:  # set()
            x[idx] = y
        return x