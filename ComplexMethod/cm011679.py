def save(
        self, *, path: str, format: Literal["binary", "unpacked"] = "binary"
    ) -> None:
        with dynamo_timed("CompiledArtifact.save"):
            if self._artifacts is None:
                raise RuntimeError(
                    "CompiledArtifact.save failed to save since there's no artifact to save"
                )
            artifact_bytes, cache_info = self._artifacts
            if len(cache_info.aot_autograd_artifacts) == 0:
                raise RuntimeError(
                    f"CompiledArtifact.save failed to save due to no aot_autograd artifacts. "
                    f"This likely means there was something that was not serializable in the "
                    f"graph passed to standalone_compile. This can generally be fixed by "
                    f"ensuring that your model only uses constructs that are serializable. "
                    f"{cache_info}"
                )
            if len(cache_info.aot_autograd_artifacts) > 1:
                raise AssertionError(
                    f"CompiledArtifact.save failed to save because there was more than one "
                    f"artifact but we only expected one. {cache_info}"
                )
            key = cache_info.aot_autograd_artifacts[0]

            if format == "binary":
                # can't assert that it is a file since it might not exist yet
                assert not os.path.isdir(path)

                from torch.utils._appending_byte_serializer import BytesWriter

                from .codecache import torch_key

                writer = BytesWriter()
                writer.write_bytes(CacheCompiledArtifact.CACHE_HEADER)
                writer.write_bytes(torch_key())
                writer.write_str(key)
                writer.write_bytes(artifact_bytes)

                from torch._inductor.codecache import write_atomic

                write_atomic(path, writer.to_bytes())
            else:
                assert format == "unpacked"
                if os.path.exists(path):
                    assert os.path.isdir(path)
                    shutil.rmtree(path, ignore_errors=True)

                from .codecache import FxGraphCache

                with temporary_cache_dir(path):
                    # This function unpacks the cache artifacts to disk
                    loaded_cache_info = torch.compiler.load_cache_artifacts(
                        artifact_bytes
                    )
                    assert loaded_cache_info is not None
                    # Now write all the output_code artifacts to disk so that
                    # they can be inspected and modified
                    for key in loaded_cache_info.inductor_artifacts:
                        subdir = FxGraphCache._get_tmp_dir_for_key(key)
                        assert os.path.exists(subdir)
                        for path in sorted(os.listdir(subdir)):
                            with open(os.path.join(subdir, path), "rb") as f:
                                graph = pickle.load(f)
                            output_file = graph.write_to_disk()
                            log.info("Output code written to: %s", output_file)