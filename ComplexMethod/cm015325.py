def test_functional_linear(self):
        with override_quantized_engine('fbgemm'):
            class FuncLinear(torch.nn.Module):
                def __init__(self, use_bias, has_relu, f_relu):
                    super().__init__()
                    self.w = torch.randn(4, 30)
                    self.b = torch.randn(4)
                    self.use_bias = use_bias
                    if has_relu:
                        if f_relu:
                            self.relu_or_id = F.relu
                        else:
                            self.relu_or_id = torch.nn.ReLU()
                    else:
                        self.relu_or_id = torch.nn.Identity()

                def forward(self, x):
                    if self.use_bias:
                        x = F.linear(x, self.w, self.b)
                    else:
                        x = F.linear(x, self.w)
                    x = self.relu_or_id(x)
                    return x

            data = (torch.rand((1, 30), dtype=torch.float),)
            quant_type_to_qlinear_fun = {
                QuantType.DYNAMIC: ns.call_function(torch.ops.quantized.linear_dynamic),
                QuantType.STATIC: ns.call_function(torch.ops.quantized.linear),
                QuantType.QAT: ns.call_function(torch.ops.quantized.linear),
            }
            quant_type_to_qlinear_relu_fun = {
                # we don't have linear_relu_dynamic
                QuantType.DYNAMIC: ns.call_function(torch.ops.quantized.linear_relu_dynamic),
                QuantType.STATIC: ns.call_function(torch.ops.quantized.linear_relu),
                QuantType.QAT: ns.call_function(torch.ops.quantized.linear_relu),
            }

            options = itertools.product(
                self.all_quant_types,
                (True, False),  # use_bias
                (True, False),  # has_relu
                (True, False),  # functional relu
            )
            for quant_type, use_bias, has_relu, f_relu in options:
                # when has_relu is False, we are using an nn.Identity and
                # we will insert observer/fake_quant for the output of nn.Identity since
                # it is a copy node, that's why we have extra observer/fake_quant
                # when has_relu is False
                quant_type_to_prepare_expected_node_occurrence = {
                    QuantType.DYNAMIC: {
                        ns.call_module(torch.ao.quantization.PlaceholderObserver): 1,
                        ns.call_module(torch.ao.quantization.MinMaxObserver): 1,
                    },
                    # There should be 3 observers: after input, weight and activation.
                    # one more observer for torch.nn.Identity when there is no relu
                    QuantType.STATIC: {
                        ns.call_module(torch.ao.quantization.HistogramObserver): 2 if has_relu else 3,
                        ns.call_module(torch.ao.quantization.PerChannelMinMaxObserver): 1,
                    },
                    # There should be 3 observers: after input, weight and activation.
                    QuantType.QAT: {
                        ns.call_module(torch.ao.quantization.FusedMovingAvgObsFakeQuantize): 3 if has_relu else 4,
                    },
                }
                model = FuncLinear(use_bias, has_relu, f_relu)
                if has_relu:
                    qlinear_fun = quant_type_to_qlinear_relu_fun[quant_type]
                else:
                    qlinear_fun = quant_type_to_qlinear_fun[quant_type]

                if quant_type != QuantType.DYNAMIC:
                    num_dequantize = 1
                else:
                    # we will have an extra quantize_per_tensor_dynamic + dequantize for
                    # nn.Identity right now, but it will be fixed after we use
                    # backend_config to configure the default pt backend
                    num_dequantize = int(not has_relu)

                convert_node_occurrence = {
                    ns.call_function(torch.quantize_per_tensor): 1 if quant_type != QuantType.DYNAMIC else 0,
                    qlinear_fun: 1,
                    ns.call_method("dequantize"): num_dequantize if quant_type != QuantType.DYNAMIC else 0,
                }
                prepare_expected_node_occurrence = \
                    quant_type_to_prepare_expected_node_occurrence[quant_type]
                result_dict = self.checkGraphModeFxOp(
                    model, data, quant_type, qlinear_fun,
                    prepare_expected_node_occurrence=prepare_expected_node_occurrence,
                    expected_node_occurrence=convert_node_occurrence)
                if quant_type != QuantType.DYNAMIC:
                    self.assertEqual(result_dict["quantized_output"], result_dict["quantized_reference_output"])
                    # Ensure packed weights in lowered models are folded
                    self.assertIn("_packed_weight_0", result_dict["quantized"].state_dict().keys())