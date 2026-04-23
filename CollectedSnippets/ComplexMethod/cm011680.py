def _prepare_load(
        *, path: str, format: Literal["binary", "unpacked"] = "binary"
    ) -> tuple[str, AbstractContextManager[Any]]:
        """
        Do format specific prep and loads, return a context manager and key
        """
        path = normalize_path_separator(path)
        with dynamo_timed("CompiledArtifact.load"):
            if format == "binary":
                # can't assert that it is a file since it might not exist yet
                assert not os.path.isdir(path)
                with open(path, "rb") as file:
                    artifacts = file.read()
                from torch.utils._appending_byte_serializer import BytesReader

                from .codecache import torch_key

                reader = BytesReader(artifacts)
                assert reader.read_bytes() == torch_key()
                key = reader.read_str()
                artifact_bytes = reader.read_bytes()
                assert reader.is_finished()

                torch.compiler.load_cache_artifacts(artifact_bytes)
                return key, nullcontext()
            else:
                assert format == "unpacked"
                assert os.path.isdir(path)
                autograd_cache_dir = os.path.join(path, "aotautograd")
                assert os.path.isdir(autograd_cache_dir)
                files = list(os.listdir(autograd_cache_dir))
                assert len(files) == 1
                key = files[0]
                cache_dir_ctx = temporary_cache_dir(path)
                return key, cache_dir_ctx