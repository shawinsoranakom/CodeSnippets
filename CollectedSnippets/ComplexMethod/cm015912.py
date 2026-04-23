def test_modify_unpacked_file(self, device: str) -> None:
        if device == GPU_TYPE and not HAS_GPU:
            raise unittest.SkipTest(f"requires {GPU_TYPE}")

        x = torch.ones(4, device=device)

        def f(x):
            with torch.no_grad():
                return 2 * x, x.sin()

        eager_out = f(x)

        with tempfile.TemporaryDirectory() as temp_dir:
            with fresh_cache():
                gm, args, kwargs = self.capture(f)(x)
                if kwargs:
                    raise AssertionError

                compiled_artifact = torch._inductor.standalone_compile(gm, args)
                compiled_out = compiled_artifact(*args)
                self.assertEqual(eager_out, compiled_out)

                compiled_artifact.save(path=temp_dir, format="unpacked")

            self.assertEqual(counters["inductor"]["fxgraph_cache_hit"], 0)

            with fresh_cache():
                # Now modify the output file and expect to see the changes
                for subdir in os.listdir(temp_dir):
                    if subdir in ["aotautograd", "fxgraph"]:
                        continue
                    subdir_path = os.path.join(temp_dir, subdir)
                    for file in os.listdir(subdir_path):
                        file_path = os.path.join(subdir_path, file)
                        if not os.path.isfile(file_path):
                            raise AssertionError
                        with open(file_path) as f:
                            file_contents = f.read()
                        if device == GPU_TYPE:
                            file_contents = file_contents.replace(
                                "2.0, tl.float32", "8.0, tl.float32"
                            )
                        else:
                            if device != "cpu":
                                raise AssertionError(f"Expected 'cpu', got {device!r}")
                            file_contents = file_contents.replace(
                                "auto tmp1 = static_cast<float>(2.0);",
                                "auto tmp1 = static_cast<float>(8.0);",
                            )
                        with open(file_path, "w") as f:
                            f.write(file_contents)

                loaded = torch._inductor.CompiledArtifact.load(
                    path=temp_dir, format="unpacked"
                )
                compiled_out = loaded(*args)
                self.assertEqual(4 * eager_out[0], compiled_out[0])

            self.assertEqual(counters["inductor"]["fxgraph_cache_hit"], 1)