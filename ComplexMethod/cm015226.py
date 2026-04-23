def test_quantize_activation_duplicate_nodes(self):
        """Test both quantize_activation_fw and quantize_activation_bw handle duplicate nodes correctly"""
        import torch.fx as fx
        from torch._functorch.partitioners import (
            quantize_activation_bw,
            quantize_activation_fw,
        )
        from torch._subclasses.fake_tensor import extract_tensor_metadata

        # Mock the inductor config
        with patch.dict(
            "torch._inductor.config.post_grad_fusion_options",
            {
                "activation_quantization_aten_pass": {
                    "allowed_dtypes": "torch.bfloat16",
                    "size_in_mb": 1,
                    "use_scaling": True,
                    "exclude_primals": False,
                    "skip_dynamo_guards": True,
                    "quantize_dynamic_shape": False,
                    "quant_type": "torch.float16",  # float8_e5m2 must be GPU
                }
            },
        ):
            # Test Forward Graph with duplicate nodes
            fwd_graph = fx.Graph()

            # Create input nodes
            x = fwd_graph.placeholder("x")
            x.meta["val"] = torch.randn(100, 100, dtype=torch.bfloat16)
            x.meta["tensor_meta"] = extract_tensor_metadata(x.meta["val"])

            y = fwd_graph.placeholder("y")
            y.meta["val"] = torch.randn(100, 100, dtype=torch.bfloat16)
            y.meta["tensor_meta"] = extract_tensor_metadata(y.meta["val"])

            # Create a computation node that will be duplicated in outputs
            mul_node = fwd_graph.call_function(torch.ops.aten.mul.Tensor, (x, y))
            mul_node.meta["val"] = torch.randn(100, 100, dtype=torch.bfloat16)
            mul_node.meta["tensor_meta"] = extract_tensor_metadata(mul_node.meta["val"])
            mul_node.meta["saved_for_quantization"] = True

            # Create another node
            add_node = fwd_graph.call_function(torch.ops.aten.add.Tensor, (x, y))
            add_node.meta["val"] = torch.randn(100, 100, dtype=torch.bfloat16)
            add_node.meta["tensor_meta"] = extract_tensor_metadata(add_node.meta["val"])

            # Create output with DUPLICATE nodes - mul_node appears at positions 0 and 2
            fwd_graph.output((mul_node, add_node, mul_node))

            # Test the forward quantization function
            quantize_activation_fw(fwd_graph)

            # Get the forward output node
            fwd_output_node = fwd_graph.find_nodes(op="output")[0]
            fwd_output_args = fwd_output_node.args[0]

            # Verify forward graph has the correct structure
            self.assertGreaterEqual(
                len(fwd_output_args), 3, "Should have at least the original 3 outputs"
            )

            # Check that positions 0 and 2 reuse the same quantized node
            pos_0_node = fwd_output_args[0]
            pos_2_node = fwd_output_args[2]

            # Both should be quantized nodes
            self.assertTrue(
                pos_0_node.name.startswith("fp8_quant_"),
                f"Position 0 should be quantized node, got: {pos_0_node.name}",
            )
            self.assertTrue(
                pos_2_node.name.startswith("fp8_quant_"),
                f"Position 2 should be quantized node, got: {pos_2_node.name}",
            )

            # The shared quantized node should have the first occurrence position in its name
            self.assertIn(
                "_pos_0",
                pos_0_node.name,
                f"Shared quantized node should have '_pos_0' in name: {pos_0_node.name}",
            )
            self.assertIn(
                "_pos_2",
                pos_2_node.name,
                f"Shared quantized node should have '_pos_2' in name: {pos_2_node.name}",
            )
            # Find scale nodes in the forward output
            fwd_scale_nodes = [
                node for node in fwd_output_args if "fp8_scale_" in node.name
            ]
            self.assertEqual(
                len(fwd_scale_nodes),
                2,
                "Should have exactly 2 scale node (shared for both quantized instances)",
            )

            # Test Backward Graph with duplicate nodes
            bwd_graph = fx.Graph()

            # Create backward placeholders corresponding to forward outputs
            quant_input1 = bwd_graph.placeholder("fp8_quant_pos_0_mul_tensor")
            quant_input1.meta["val"] = torch.randn(100, 100, dtype=torch.float16)
            quant_input1.meta["tensor_meta"] = extract_tensor_metadata(
                quant_input1.meta["val"]
            )
            quant_input1.meta["saved_for_quantization"] = True
            quant_input1.meta["dequant_type"] = torch.bfloat16

            add_input = bwd_graph.placeholder("add")
            add_input.meta["val"] = torch.randn(100, 100, dtype=torch.bfloat16)
            add_input.meta["tensor_meta"] = extract_tensor_metadata(
                add_input.meta["val"]
            )

            quant_input2 = bwd_graph.placeholder("fp8_quant_pos_2_mul_tensor")
            quant_input2.meta["val"] = torch.randn(100, 100, dtype=torch.float16)
            quant_input2.meta["tensor_meta"] = extract_tensor_metadata(
                quant_input2.meta["val"]
            )
            quant_input2.meta["saved_for_quantization"] = True
            quant_input2.meta["dequant_type"] = torch.bfloat16

            # Add scale node (would come from forward)
            scale_input = bwd_graph.placeholder("fp8_scale_pos_0_mul_tensor")
            scale_input.meta["val"] = torch.randn(100, 100, dtype=torch.float32)
            scale_input.meta["tensor_meta"] = extract_tensor_metadata(
                scale_input.meta["val"]
            )

            scale_input2 = bwd_graph.placeholder("fp8_scale_pos_2_mul_tensor")
            scale_input2.meta["val"] = torch.randn(100, 100, dtype=torch.float32)
            scale_input2.meta["tensor_meta"] = extract_tensor_metadata(
                scale_input.meta["val"]
            )
            # Create some backward computation using both quantized inputs
            grad_output1 = bwd_graph.placeholder("tangents_1")
            grad_output1.meta["val"] = torch.randn(100, 100, dtype=torch.bfloat16)
            grad_output1.meta["tensor_meta"] = extract_tensor_metadata(
                grad_output1.meta["val"]
            )

            grad_output2 = bwd_graph.placeholder("tangents_2")
            grad_output2.meta["val"] = torch.randn(100, 100, dtype=torch.bfloat16)
            grad_output2.meta["tensor_meta"] = extract_tensor_metadata(
                grad_output2.meta["val"]
            )

            # Create backward operations using the quantized inputs
            mul_bwd1 = bwd_graph.call_function(
                torch.ops.aten.mul.Tensor, (quant_input1, grad_output1)
            )
            mul_bwd1.meta["val"] = torch.randn(100, 100, dtype=torch.bfloat16)
            mul_bwd1.meta["tensor_meta"] = extract_tensor_metadata(mul_bwd1.meta["val"])

            mul_bwd2 = bwd_graph.call_function(
                torch.ops.aten.mul.Tensor, (quant_input2, grad_output2)
            )
            mul_bwd2.meta["val"] = torch.randn(100, 100, dtype=torch.bfloat16)
            mul_bwd2.meta["tensor_meta"] = extract_tensor_metadata(mul_bwd2.meta["val"])

            # Create output
            bwd_graph.output((mul_bwd1, mul_bwd2))

            # Test the backward quantization function
            quantize_activation_bw(bwd_graph)

            # Verify backward graph processing
            bwd_placeholders = list(bwd_graph.find_nodes(op="placeholder"))
            quantized_placeholders = [
                p for p in bwd_placeholders if "fp8_quant_" in p.name
            ]
            scale_placeholders = [p for p in bwd_placeholders if "fp8_scale_" in p.name]

            # Should have processed the quantized placeholders
            self.assertGreater(
                len(quantized_placeholders), 0, "Should have quantized placeholders"
            )
            self.assertGreater(
                len(scale_placeholders), 0, "Should have scale placeholders"
            )

            # Check that dequantization operations were added
            dequant_operations = [
                node
                for node in bwd_graph.nodes
                if node.op == "call_function"
                and "convert_element_type" in str(node.target)
            ]

            # Should have dequantization operations for each quantized input that was processed
            self.assertGreater(
                len(dequant_operations),
                0,
                "Should have dequantization operations in backward graph",
            )

            # Verify the backward graph users were properly updated
            for quant_placeholder in quantized_placeholders:
                # The quantized placeholder should not be directly used in final operations
                # (it should be replaced by dequantized versions)
                direct_users = [
                    user
                    for user in quant_placeholder.users
                    if user.op == "call_function" and "mul" in str(user.target)
                ]
                # Direct usage should be minimal (only for dequantization chain)
                self.assertLessEqual(
                    len(direct_users),
                    1,
                    f"Quantized placeholder {quant_placeholder.name} should have minimal direct users",
                )