def formatter(arg):
            # Format any instance of `Tensor` (standalone, in list, or in dict)
            # by Tensor[TensorShape]
            # Eg. Tensor with shape (3, 4) is formatted as Tensor[3, 4]
            if isinstance(arg, torch.Tensor):
                shape = str(tuple(arg.shape))
                dtype = str(arg.dtype)
                device = str(arg.device)
                contiguity_suffix = ""
                # NB: sparse CSR tensors annoyingly return is_sparse=False
                is_sparse = arg.is_sparse or arg.layout == torch.sparse_csr
                if not is_sparse and not arg.is_contiguous():
                    contiguity_suffix = ", contiguous=False"
                return f'Tensor[size={shape}, device="{device}", dtype={dtype}{contiguity_suffix}]'
            elif isinstance(arg, dict):
                return {k: formatter(v) for k, v in arg.items()}
            elif is_iterable_of_tensors(arg):
                return "TensorList[" + ", ".join(map(formatter, arg)) + "]"
            elif isinstance(arg, (list, tuple)):  # Handle list, tuple
                return "(" + ",".join(map(formatter, arg)) + ")"

            return repr(arg)