def get_opoverloadpacket_from_dispatch(kernel):
            # Skip cumulative operations - they're in ReduceOps.cpp but aren't reductions
            if kernel in ("cumsum", "cumprod", "logcumsumexp", "xor_sum"):
                return None

            # Special mappings for ambiguous kernel names
            if kernel == "and":
                return "all"
            if kernel == "or":
                return "any"

            if hasattr(torch.ops.aten, kernel):
                return kernel
            if hasattr(torch.ops.aten, f"__{kernel}__"):
                return f"__{kernel}__"
            if hasattr(torch.ops.aten, f"special_{kernel}"):
                return f"special_{kernel}"
            if "_" in kernel:
                kernel_split = kernel.split("_")
                new_kernel = "_".join(kernel_split[:-1])
                if hasattr(torch.ops.aten, new_kernel):
                    return new_kernel

            # could not find op from kernel dispatch string
            return None