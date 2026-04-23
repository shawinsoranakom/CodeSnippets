def test_basic(
        self,
        device: str,
        format: str,
        dynamic: bool,
        graph_partition: bool,
        is_aot: bool,
    ) -> None:
        if device == GPU_TYPE and not HAS_GPU:
            raise unittest.SkipTest(f"requires {GPU_TYPE}")

        # AOT mode does not support unpacked format
        if is_aot and format == "unpacked":
            raise unittest.SkipTest("AOT mode does not support unpacked format")

        mod = torch.nn.Linear(1, 3, device=device)
        x = torch.randn(4, 1, device=device)
        if dynamic:
            torch._dynamo.mark_dynamic(x, 0)

        def f(x):
            with torch.no_grad():
                return mod(x), x.sin()

        eager_out = f(x)

        with (
            tempfile.TemporaryDirectory() as temp_dir,
            config.patch(graph_partition=graph_partition),
        ):
            path = (
                temp_dir
                if format == "unpacked"
                else os.path.join(temp_dir, "compiled_artifact.bin")
            )
            with fresh_cache():
                gm, args, kwargs = self.capture(f)(x)
                if kwargs:
                    raise AssertionError

                compiled_artifact = torch._inductor.standalone_compile(
                    gm, args, aot=is_aot
                )
                compiled_artifact.save(path=path, format=format)

            self.assertEqual(counters["inductor"]["fxgraph_cache_hit"], 0)

            with fresh_cache():
                loaded = torch._inductor.CompiledArtifact.load(path=path, format=format)
                if dynamic:
                    concrete_args = [
                        4 if isinstance(a, torch.SymInt) else a for a in args
                    ]
                else:
                    concrete_args = args
                compiled_out = loaded(*concrete_args)
                self.assertEqual(eager_out, compiled_out)

            if not is_aot:
                self.assertEqual(counters["inductor"]["fxgraph_cache_hit"], 1)