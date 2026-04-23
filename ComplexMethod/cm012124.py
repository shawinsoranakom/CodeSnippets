def collect(
        cls,
    ) -> tuple[TritonBundle, TritonBundlerMetadata | None]:
        """
        This is the main function called when a cache write happens. This function
        converts all the previously remembered kernels into bundled format so that
        it can be written into a cache entry.
        This function also finalizes the current bundle.
        """
        from torch._inductor import config

        if not TritonBundler.is_enabled():
            cls.end_compile()
            set_feature_use("triton_bundling", False)
            return TritonBundle([], []), None
        set_feature_use("triton_bundling", True)

        with dynamo_timed(key="TritonBundler.collect", log_pt2_compile_event=True):
            entries = cls._entries
            if entries is not None:
                # Only bundle winning autotuning configs. If _winners is
                # non-empty, skip entries whose kernel_hash is not a winner.
                # When _winners is empty (single-config kernels, or no
                # autotuning ran), bundle everything.
                winners = cls._winners
                result: list[TritonKernelArtifacts] = []
                kernel_names: list[str] = []
                for entry in entries:
                    if winners and entry.kernel_hash not in winners:
                        log.debug("Skipping non-winning kernel %s", entry.kernel_hash)
                        continue
                    artifacts: list[TritonKernelArtifact] = []
                    path = os.path.join(entry.directory, entry.kernel_hash)
                    if not os.path.exists(path):
                        continue
                    for filename in os.listdir(path):
                        filepath = os.path.join(path, filename)
                        try:
                            assert os.path.isfile(filepath)
                            with open(filepath, "rb") as file:
                                payload = file.read()
                                if filepath.endswith(".json"):
                                    # Make sure there's no sentinel value
                                    if TritonBundler._REPLACE_BYTES in payload:
                                        log.warning(
                                            "Bundle contains illegal %s, payload: %s",
                                            TritonBundler._REPLACE_BYTES,
                                            payload,
                                        )
                                        raise AssertionError(
                                            "Bundle contains illegal bytes"
                                        )
                                    # Remove the path from payload
                                    payload = payload.replace(
                                        str.encode(path), TritonBundler._REPLACE_BYTES
                                    )
                                artifacts.append(
                                    TritonKernelArtifact(filename, payload)
                                )
                            counters["inductor"]["triton_bundler_save_kernel"] += 1
                        except Exception:
                            log.debug("failed to collect triton kernel", exc_info=True)
                        extension = os.path.splitext(filename)[1]
                        if extension in GPU_KERNEL_BIN_EXTS.values():
                            # Each kernel has bunch of files like .cubin(for cuda), .zebin(for xpu), .json, .ttir
                            # Just append one of them without the extension
                            kernel_names.append(Path(filename).stem)
                    if artifacts:
                        result.append(
                            TritonKernelArtifacts(
                                entry.kernel_hash,
                                entry.device,
                                artifacts,
                            )
                        )
                if config.use_static_triton_launcher:
                    static_autotuners, static_kernel_names = (
                        cls.collect_static_autotuners()
                    )
                else:
                    static_autotuners = []
                    static_kernel_names = []
                cls.end_compile()
                return TritonBundle(result, static_autotuners), TritonBundlerMetadata(
                    kernel_names, static_kernel_names
                )
            return TritonBundle([], []), None