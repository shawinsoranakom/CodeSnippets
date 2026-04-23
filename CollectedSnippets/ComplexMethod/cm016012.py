def _get_multi_index(self, arr, indices):
        """Mimic multi dimensional indexing.

        Parameters
        ----------
        arr : ndarray
            Array to be indexed.
        indices : tuple of index objects

        Returns
        -------
        out : ndarray
            An array equivalent to the indexing operation (but always a copy).
            `arr[indices]` should be identical.
        no_copy : bool
            Whether the indexing operation requires a copy. If this is `True`,
            `np.may_share_memory(arr, arr[indices])` should be `True` (with
            some exceptions for scalars and possibly 0-d arrays).

        Notes
        -----
        While the function may mostly match the errors of normal indexing this
        is generally not the case.
        """
        in_indices = list(indices)
        indices = []
        # if False, this is a fancy or boolean index
        no_copy = True
        # number of fancy/scalar indexes that are not consecutive
        num_fancy = 0
        # number of dimensions indexed by a "fancy" index
        fancy_dim = 0
        # NOTE: This is a funny twist (and probably OK to change).
        # The boolean array has illegal indexes, but this is
        # allowed if the broadcast fancy-indices are 0-sized.
        # This variable is to catch that case.
        error_unless_broadcast_to_empty = False

        # We need to handle Ellipsis and make arrays from indices, also
        # check if this is fancy indexing (set no_copy).
        ndim = 0
        ellipsis_pos = None  # define here mostly to replace all but first.
        for i, indx in enumerate(in_indices):  # codespell:ignore
            if indx is None:  # codespell:ignore
                continue
            if isinstance(indx, np.ndarray) and indx.dtype == bool:  # codespell:ignore
                no_copy = False
                if indx.ndim == 0:  # codespell:ignore
                    raise IndexError
                # boolean indices can have higher dimensions
                ndim += indx.ndim  # codespell:ignore
                fancy_dim += indx.ndim  # codespell:ignore
                continue
            if indx is Ellipsis:  # codespell:ignore
                if ellipsis_pos is None:
                    ellipsis_pos = i
                    continue  # do not increment ndim counter
                raise IndexError
            if isinstance(indx, slice):  # codespell:ignore
                ndim += 1
                continue
            if not isinstance(indx, np.ndarray):  # codespell:ignore
                # This could be open for changes in numpy.
                # numpy should maybe raise an error if casting to intp
                # is not safe. It rejects np.array([1., 2.]) but not
                # [1., 2.] as index (same for ie. np.take).
                # (Note the importance of empty lists if changing this here)
                try:
                    indx = np.array(indx, dtype=np.intp)  # codespell:ignore
                except ValueError:
                    raise IndexError from None
                in_indices[i] = indx  # codespell:ignore
            elif indx.dtype.kind != "b" and indx.dtype.kind != "i":  # codespell:ignore
                raise IndexError(
                    "arrays used as indices must be of integer (or boolean) type"
                )
            if indx.ndim != 0:  # codespell:ignore
                no_copy = False
            ndim += 1
            fancy_dim += 1

        if arr.ndim - ndim < 0:
            # we can't take more dimensions then we have, not even for 0-d
            # arrays.  since a[()] makes sense, but not a[(),]. We will
            # raise an error later on, unless a broadcasting error occurs
            # first.
            raise IndexError

        if ndim == 0 and None not in in_indices:
            # Well we have no indexes or one Ellipsis. This is legal.
            return arr.copy(), no_copy

        if ellipsis_pos is not None:
            in_indices[ellipsis_pos : ellipsis_pos + 1] = [slice(None, None)] * (
                arr.ndim - ndim
            )

        for ax, indx in enumerate(in_indices):  # codespell:ignore
            if isinstance(indx, slice):  # codespell:ignore
                # convert to an index array
                indx = np.arange(*indx.indices(arr.shape[ax]))  # codespell:ignore
                indices.append(["s", indx])  # codespell:ignore
                continue
            elif indx is None:  # codespell:ignore
                # this is like taking a slice with one element from a new axis:
                indices.append(["n", np.array([0], dtype=np.intp)])
                arr = arr.reshape(arr.shape[:ax] + (1,) + arr.shape[ax:])
                continue
            if isinstance(indx, np.ndarray) and indx.dtype == bool:  # codespell:ignore
                if indx.shape != arr.shape[ax : ax + indx.ndim]:  # codespell:ignore
                    raise IndexError

                try:
                    flat_indx = np.ravel_multi_index(
                        np.nonzero(indx),  # codespell:ignore
                        arr.shape[ax : ax + indx.ndim],  # codespell:ignore
                        mode="raise",
                    )
                except Exception:
                    error_unless_broadcast_to_empty = True
                    # fill with 0s instead, and raise error later
                    flat_indx = np.array(
                        [0] * indx.sum(),  # codespell:ignore
                        dtype=np.intp,
                    )
                # concatenate axis into a single one:
                if indx.ndim != 0:  # codespell:ignore
                    arr = arr.reshape(
                        arr.shape[:ax]
                        + (np.prod(arr.shape[ax : ax + indx.ndim]),)  # codespell:ignore
                        + arr.shape[ax + indx.ndim :]  # codespell:ignore
                    )
                    indx = flat_indx  # codespell:ignore
                else:
                    # This could be changed, a 0-d boolean index can
                    # make sense (even outside the 0-d indexed array case)
                    # Note that originally this is could be interpreted as
                    # integer in the full integer special case.
                    raise IndexError
            else:
                # If the index is a singleton, the bounds check is done
                # before the broadcasting. This used to be different in <1.9
                if indx.ndim == 0:  # codespell:ignore
                    if (
                        indx >= arr.shape[ax]  # codespell:ignore
                        or indx < -arr.shape[ax]  # codespell:ignore
                    ):
                        raise IndexError
            if indx.ndim == 0:  # codespell:ignore
                # The index is a scalar. This used to be two fold, but if
                # fancy indexing was active, the check was done later,
                # possibly after broadcasting it away (1.7. or earlier).
                # Now it is always done.
                if indx >= arr.shape[ax] or indx < -arr.shape[ax]:  # codespell:ignore
                    raise IndexError
            if len(indices) > 0 and indices[-1][0] == "f" and ax != ellipsis_pos:
                # NOTE: There could still have been a 0-sized Ellipsis
                # between them. Checked that with ellipsis_pos.
                indices[-1].append(indx)  # codespell:ignore
            else:
                # We have a fancy index that is not after an existing one.
                # NOTE: A 0-d array triggers this as well, while one may
                # expect it to not trigger it, since a scalar would not be
                # considered fancy indexing.
                num_fancy += 1
                indices.append(["f", indx])  # codespell:ignore

        if num_fancy > 1 and not no_copy:
            # We have to flush the fancy indexes left
            new_indices = indices[:]
            axes = list(range(arr.ndim))
            fancy_axes = []
            new_indices.insert(0, ["f"])
            ni = 0
            ai = 0
            for indx in indices:  # codespell:ignore
                ni += 1
                if indx[0] == "f":  # codespell:ignore
                    new_indices[0].extend(indx[1:])  # codespell:ignore
                    del new_indices[ni]
                    ni -= 1
                    for ax in range(ai, ai + len(indx[1:])):  # codespell:ignore
                        fancy_axes.append(ax)
                        axes.remove(ax)
                ai += len(indx) - 1  # axis we are at # codespell:ignore
            indices = new_indices
            # and now we need to transpose arr:
            arr = arr.transpose(*(fancy_axes + axes))

        # We only have one 'f' index now and arr is transposed accordingly.
        # Now handle newaxis by reshaping...
        ax = 0
        for indx in indices:  # codespell:ignore
            if indx[0] == "f":  # codespell:ignore
                if len(indx) == 1:  # codespell:ignore
                    continue
                # First of all, reshape arr to combine fancy axes into one:
                orig_shape = arr.shape
                orig_slice = orig_shape[ax : ax + len(indx[1:])]  # codespell:ignore
                arr = arr.reshape(
                    arr.shape[:ax]
                    + (np.prod(orig_slice).astype(int),)
                    + arr.shape[ax + len(indx[1:]) :]  # codespell:ignore
                )

                # Check if broadcasting works
                res = np.broadcast(*indx[1:])  # codespell:ignore
                # unfortunately the indices might be out of bounds. So check
                # that first, and use mode='wrap' then. However only if
                # there are any indices...
                if res.size != 0:
                    if error_unless_broadcast_to_empty:
                        raise IndexError
                    for _indx, _size in zip(indx[1:], orig_slice):  # codespell:ignore
                        if _indx.size == 0:
                            continue
                        if np.any(_indx >= _size) or np.any(_indx < -_size):
                            raise IndexError
                if len(indx[1:]) == len(orig_slice):  # codespell:ignore
                    if np.prod(orig_slice) == 0:
                        # Work around for a crash or IndexError with 'wrap'
                        # in some 0-sized cases.
                        try:
                            mi = np.ravel_multi_index(
                                indx[1:],  # codespell:ignore
                                orig_slice,
                                mode="raise",  # codespell:ignore
                            )
                        except Exception as exc:
                            # This happens with 0-sized orig_slice (sometimes?)
                            # here it is a ValueError, but indexing gives a:
                            raise IndexError("invalid index into 0-sized") from exc
                    else:
                        mi = np.ravel_multi_index(
                            indx[1:],  # codespell:ignore
                            orig_slice,
                            mode="wrap",
                        )
                else:
                    # Maybe never happens...
                    raise ValueError
                arr = arr.take(mi.ravel(), axis=ax)
                try:
                    arr = arr.reshape(arr.shape[:ax] + mi.shape + arr.shape[ax + 1 :])
                except ValueError:
                    # too many dimensions, probably
                    raise IndexError from None
                ax += mi.ndim
                continue

            # If we are here, we have a 1D array for take:
            arr = arr.take(indx[1], axis=ax)  # codespell:ignore
            ax += 1

        return arr, no_copy