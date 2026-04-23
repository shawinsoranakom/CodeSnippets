def test_reduction_tag_coverage(self):
        """Test that operators with reduction tag are from reduction operator files."""
        pytorch_dir = os.path.abspath(__file__ + "/../../")
        files = [
            "aten/src/ATen/native/ReduceOps.cpp",
            "aten/src/ATen/native/ReduceAllOps.h",
        ]

        # Operators that are not pure reduction but have reduction overloads
        allowed_functions = (
            # min/max have both elementwise (binary) and reduction versions
            "aten.min.other",
            "aten.min.out",
            "aten.max.other",
            "aten.max.out",
        )

        regex = re.compile(r"DEFINE_DISPATCH\(.*_stub")

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

        for file_name in files:
            file_path = os.path.join(pytorch_dir, file_name)
            if not os.path.exists(file_path):
                continue

            with open(file_path) as f:
                lines = f.read()
                matches = regex.findall(lines)
                for match in matches:
                    kernel = match[len("DEFINE_DISPATCH(") : -len("_stub")]

                    kernel = get_opoverloadpacket_from_dispatch(kernel)
                    if kernel is None:
                        continue

                    overloadpacket = getattr(torch.ops.aten, kernel)

                    for overload_name in overloadpacket.overloads():
                        overload = getattr(overloadpacket, overload_name)

                        if not torch._C._dispatch_has_kernel(overload.name()):
                            continue

                        # TODO: tags are not propagated to generated overload,
                        # and there's no way of specifying them
                        if torch.Tag.generated in overload.tags:
                            continue

                        if str(overload) in allowed_functions:
                            continue

                        self.assertTrue(
                            torch.Tag.reduction in overload.tags,
                            f"{overload} should have reduction tag",
                        )