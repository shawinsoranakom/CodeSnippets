def _get_conv_linear_test_cases(self, is_reference):
        """ Returns a list of test cases, with format:
        is_dynamic, ModuleClass, module_constructor_inputs,
        inputs, quantized_node, weight_prepack_op
        """
        class FunctionalConv1d(torch.nn.Module):
            def __init__(self, weight):
                super().__init__()
                self.weight = torch.nn.Parameter(weight)
                self.stride = 1
                self.padding = 0
                self.dilation = 1
                self.groups = 1

            def forward(self, x):
                return F.conv1d(x, self.weight, None, self.stride, self.padding, self.dilation, self.groups)


        class Conv1d(torch.nn.Module):
            def __init__(self, *args):
                super().__init__()
                self.conv = torch.nn.Conv1d(*args)

            def forward(self, x):
                return self.conv(x)

        conv1d_input = torch.rand(1, 3, 224)
        conv1d_weight = torch.rand(3, 3, 3)
        conv1d_module_args = (3, 3, 3)

        class FunctionalConv2d(torch.nn.Module):
            def __init__(self, weight):
                super().__init__()
                self.weight = torch.nn.Parameter(weight)
                self.stride = (1, 1)
                self.padding = (0, 0)
                self.dilation = (1, 1)
                self.groups = 1

            def forward(self, x):
                return F.conv2d(x, self.weight, None, self.stride, self.padding, self.dilation, self.groups)

        class Conv2d(torch.nn.Module):
            def __init__(self, *args):
                super().__init__()
                self.conv = torch.nn.Conv2d(*args)

            def forward(self, x):
                return self.conv(x)

        conv2d_input = torch.rand(1, 3, 224, 224)
        conv2d_weight = torch.rand(3, 3, 3, 3)
        conv2d_module_args = (3, 3, 3)

        class FunctionalConv3d(torch.nn.Module):
            def __init__(self, weight):
                super().__init__()
                self.weight = torch.nn.Parameter(weight)
                self.stride = (1, 1, 1)
                self.padding = (0, 0, 0)
                self.dilation = (1, 1, 1)
                self.groups = 1

            def forward(self, x):
                return F.conv3d(
                    x,
                    self.weight,
                    None,
                    self.stride,
                    self.padding,
                    self.dilation,
                    self.groups,
                )

        class Conv3d(torch.nn.Module):
            def __init__(self, *args):
                super().__init__()
                self.conv = torch.nn.Conv3d(*args)

            def forward(self, x):
                return self.conv(x)

        conv3d_input = torch.rand(1, 3, 32, 224, 224)
        conv3d_weight = torch.rand(3, 3, 3, 3, 3)
        conv3d_module_args = (3, 3, 3)

        class Linear(torch.nn.Module):
            def __init__(self, weight):
                super().__init__()
                self.weight = torch.nn.Parameter(weight)

            def forward(self, x):
                return F.linear(x, self.weight)

        linear_input = torch.rand(8, 5)
        linear_weight = torch.rand(10, 5)

        class LinearModule(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.linear = torch.nn.Linear(5, 10)

            def forward(self, x):
                return self.linear(x)

        linear_module_input = torch.rand(8, 5)

        # is_dynamic, ModuleClass, module_constructor_inputs,
        # inputs, quantized_node, weight_prepack_node
        tests = [
            (
                False,
                FunctionalConv1d,
                (conv1d_weight,),
                (conv1d_input,),
                ns.call_function(torch.nn.functional.conv1d if is_reference else torch.ops.quantized.conv1d) ,
                ns.call_function(torch.ops.quantized.conv1d_prepack),
            ),
            (
                False,
                FunctionalConv2d,
                (conv2d_weight,),
                (conv2d_input,),
                ns.call_function(torch.nn.functional.conv2d if is_reference else torch.ops.quantized.conv2d),
                ns.call_function(torch.ops.quantized.conv2d_prepack),
            ),
            (
                False,
                FunctionalConv3d,
                (conv3d_weight,),
                (conv3d_input,),
                ns.call_function(torch.nn.functional.conv3d if is_reference else torch.ops.quantized.conv3d),
                ns.call_function(torch.ops.quantized.conv3d_prepack),
            ),
            (
                False,
                Conv1d,
                conv1d_module_args,
                (conv1d_input,),
                ns.call_module(nnqr.Conv1d if is_reference else nnq.Conv1d),
                None
            ),
            (
                False,
                Conv2d,
                conv2d_module_args,
                (conv2d_input,),
                ns.call_module(nnqr.Conv2d if is_reference else nnq.Conv2d),
                None
            ),
            (
                False,
                Conv3d,
                conv3d_module_args,
                (conv3d_input,),
                ns.call_module(nnqr.Conv3d if is_reference else nnq.Conv3d),
                None
            ),
            (
                True,
                Linear,
                (linear_weight,),
                (linear_input,),
                None if is_reference else ns.call_function(torch.ops.quantized.linear_dynamic),
                ns.call_function(torch.ops.quantized.linear_prepack),
            ),
            (
                False,
                Linear,
                (linear_weight,),
                (linear_input,),
                ns.call_function(torch.nn.functional.linear if is_reference else torch.ops.quantized.linear),
                ns.call_function(torch.ops.quantized.linear_prepack),
            ),
            (
                True,
                LinearModule,
                (),
                (linear_module_input,),
                ns.call_module(nnqr.Linear) if is_reference else ns.call_module(nnqd.Linear),
                None,
            ),
            (
                False,
                LinearModule,
                (),
                (linear_module_input,),
                ns.call_module(nnqr.Linear if is_reference else nnq.Linear),
                None,
            ),
        ]
        return tests