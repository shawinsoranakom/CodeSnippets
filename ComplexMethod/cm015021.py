def test_pointwise_tag_coverage(self):
        pytorch_dir = os.path.abspath(__file__ + "/../../")
        files = [
            "aten/src/ATen/native/UnaryOps.cpp",
            "aten/src/ATen/native/BinaryOps.cpp",
            "aten/src/ATen/native/PointwiseOps.cpp",
            "aten/src/ATen/native/TensorCompare.cpp",
        ]

        allowed_functions = (
            # reduction version of these operators
            "aten.max.default",
            "aten.max.dim",
            "aten.max.dim_max",
            "aten.max.names_dim",
            "aten.max.names_dim_max",
            "aten.max.unary_out",
            "aten.min.default",
            "aten.min.dim",
            "aten.min.dim_min",
            "aten.min.names_dim",
            "aten.min.names_dim_min",
            "aten.min.unary_out",
            # not pointwise
            "aten.isin.Tensor_Tensor",
            "aten.isin.Tensor_Tensor_out",
            "aten.isin.Tensor_Scalar",
            "aten.isin.Tensor_Scalar_out",
            "aten.isin.Scalar_Tensor",
            "aten.isin.Scalar_Tensor_out",
            "aten.mode.default",
            "aten.mode.dimname",
            "aten.mode.dimname_out",
            "aten.mode.values",
        )

        regex = re.compile(r"DEFINE_DISPATCH\(.*_stub")

        def get_opoverloadpacket_from_dispatch(kernel):
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
            self.assertTrue(False)

        for file_name in files:
            with open(os.path.join(pytorch_dir, file_name)) as f:
                lines = f.read()
                matches = regex.findall(lines)
                for match in matches:
                    kernel = match[len("DEFINE_DISPATCH(") : -len("_stub")]

                    # no op definition for it, but defined with DEFINE_DISPATCH ?
                    if kernel == "trigamma":
                        continue

                    kernel = get_opoverloadpacket_from_dispatch(kernel)
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

                        self.assertTrue(torch.Tag.pointwise in overload.tags)