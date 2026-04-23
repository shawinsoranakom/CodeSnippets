def test_triton_hop(self) -> None:
        @triton.jit
        def add_kernel(
            in_ptr0,
            in_ptr1,
            out_ptr,
            n_elements,
            fval,
            ival,
            BLOCK_SIZE: "tl.constexpr",
        ):
            pid = tl.program_id(axis=0)
            block_start = pid * BLOCK_SIZE
            offsets = block_start + tl.arange(0, BLOCK_SIZE)
            mask = offsets < n_elements
            x = tl.load(in_ptr0 + offsets, mask=mask)
            y = tl.load(in_ptr1 + offsets, mask=mask)
            output = x + y + fval + ival
            tl.store(out_ptr + offsets, output, mask=mask)

        def custom_add(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
            output = torch.empty_like(x)
            n_elements = output.numel()

            def grid(meta):
                return (triton.cdiv(n_elements, meta["BLOCK_SIZE"]),)

            wrap_triton(add_kernel)[grid](
                x, y, output, n_elements, 3.14, 42, BLOCK_SIZE=16
            )

            return output

        class MyModel(torch.nn.Module):
            def forward(self, x, y):
                return custom_add(x, y)

        def custom_add_autotune(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
            output = torch.empty_like(x)
            n_elements = output.numel()

            def grid(meta):
                return (triton.cdiv(n_elements, meta["BLOCK_SIZE"]),)

            wrap_triton(add_kernel)[grid](
                x, y, output, n_elements, 3.14, 42, BLOCK_SIZE=16, num_warps=8
            )

            return output

        class MyModelAutotune(torch.nn.Module):
            def forward(self, x, y):
                return custom_add_autotune(x, y)

        device = "cuda"

        for m in [MyModel().to(device), MyModelAutotune().to(device)]:
            args = (torch.randn(3, device=device), torch.randn(3, device=device))
            ep = torch.export.export(m, args=args)
            ep = ep.run_decompositions(decompose_custom_triton_ops=False)
            if not torch.allclose(m(*args), ep.module()(*args)):
                raise AssertionError(
                    "Exported model output does not match eager output"
                )

            serialized = ExportedProgramSerializer().serialize(ep)

            for node in serialized.exported_program.graph_module.graph.nodes:
                if (
                    node.target
                    == "torch.ops.higher_order.triton_kernel_wrapper_functional"
                ):
                    triton_node = node

            self.assertIsNotNone(triton_node)

            args = []
            kwargs = {}

            for arg in triton_node.inputs:
                if arg.kind == ArgumentKind.POSITIONAL:
                    args.append(arg.arg)
                elif arg.kind == ArgumentKind.KEYWORD:
                    kwargs[arg.name] = arg.arg

            self.assertEqual(len(args), 6)
            # Always: name, grid, output_indices and num_warps are
            # Triton version dependent: num_cpu_threads, shared_memory_bytes
            self.assertTrue(len(kwargs) >= 4)

            for i in range(3):
                self.assertIsNotNone(args[i].as_tensor)

            self.assertEqual(args[3].as_int, 3)
            self.assertAlmostEqual(args[4].as_float, 3.14, places=2)
            self.assertEqual(args[5].as_int, 42)
            kernel_name = kwargs["name"].as_string
            symbol_name = kernel_name.rpartition("_")[0]
            self.assertEqual(symbol_name, "add_kernel")
            self.assertEqual(kwargs["grid"].as_ints, [1, 1, 1])
            self.assertEqual(kwargs["output_indices"].as_ints, [2])
            self.assertEqual(
                kwargs["num_warps"].as_int, 8 if isinstance(m, MyModelAutotune) else 4
            )

            if "num_cpu_threads" in kwargs:
                self.assertEqual(kwargs["num_cpu_threads"].as_int, 0)
            if "shared_memory_bytes" in kwargs:
                self.assertEqual(kwargs["shared_memory_bytes"].as_int, 0)

            self.assertEqual(len(triton_node.outputs), 1)
            self.assertIsNotNone(triton_node.outputs[0].as_tensors)
            self.assertEqual(
                len(triton_node.outputs[0].as_tensors),
                len(kwargs["output_indices"].as_ints),
            )
            self.assertEqual(triton_node.outputs[0].as_tensors[0].name, "getitem")

            with self.assertRaisesRegex(
                SerializeError,
                "deserialize nyi for torch._higher_order_ops.triton_kernel_wrap.triton_kernel_wrapper_functional",
            ):
                ExportedProgramDeserializer().deserialize(
                    serialized.exported_program,
                    serialized.state_dict,
                    serialized.constants,
                    serialized.example_inputs,
                )