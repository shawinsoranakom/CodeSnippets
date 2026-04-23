def _combine_masks(method, t, mask):
            r"""Combine the masks from all pruning methods and returns a new mask.

            Args:
                method (a BasePruningMethod subclass): pruning method
                    currently being applied.
                t (torch.Tensor): tensor representing the parameter to prune
                    (of same dimensions as mask).
                mask (torch.Tensor): mask from previous pruning iteration

            Returns:
                new_mask (torch.Tensor): new mask that combines the effects
                    of the old mask and the new mask from the current
                    pruning method (of same dimensions as mask and t).
            """
            new_mask = mask  # start off from existing mask
            new_mask = new_mask.to(dtype=t.dtype)

            # compute a slice of t onto which the new pruning method will operate
            if method.PRUNING_TYPE == "unstructured":
                # prune entries of t where the mask is 1
                slc = mask == 1

            # for struct pruning, exclude channels that have already been
            # entirely pruned
            elif method.PRUNING_TYPE == "structured":
                if not hasattr(method, "dim"):
                    raise AttributeError(
                        "Pruning methods of PRUNING_TYPE "
                        '"structured" need to have the attribute `dim` defined.'
                    )

                # find the channels to keep by removing the ones that have been
                # zeroed out already (i.e. where sum(entries) == 0)
                n_dims = t.dim()  # "is this a 2D tensor? 3D? ..."
                dim = method.dim
                # convert negative indexing
                if dim < 0:
                    dim = n_dims + dim
                # if dim is still negative after subtracting it from n_dims
                if dim < 0:
                    raise IndexError(
                        f"Index is out of bounds for tensor with dimensions {n_dims}"
                    )
                # find channels along dim = dim that aren't already tots 0ed out
                keep_channel = mask.sum(dim=[d for d in range(n_dims) if d != dim]) != 0
                # create slice to identify what to prune
                slc = [slice(None)] * n_dims
                slc[dim] = keep_channel

            elif method.PRUNING_TYPE == "global":
                n_dims = len(t.shape)  # "is this a 2D tensor? 3D? ..."
                slc = [slice(None)] * n_dims

            else:
                raise ValueError(f"Unrecognized PRUNING_TYPE {method.PRUNING_TYPE}")

            # compute the new mask on the unpruned slice of the tensor t
            if isinstance(slc, list):
                slc = tuple(slc)
            partial_mask = method.compute_mask(t[slc], default_mask=mask[slc])
            new_mask[slc] = partial_mask.to(dtype=new_mask.dtype)

            return new_mask