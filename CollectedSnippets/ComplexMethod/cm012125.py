def read_and_emit(bundle: TritonBundle) -> TritonBundlerMetadata | None:
        """
        This is the main function called when a cache read happens. This function
        converts the bundled format back into individual files and writes them
        to the filesystem.

        NOTE: When we are writing to the filesystem, we assume exclusive access
        to the target directory.
        This means that if the target folder already exists and is non-empty,
        we bail out.
        Exclusive access means that no other process should be writing to
        or reading from the target directory.
        """
        from torch._inductor import config

        if not TritonBundler.is_enabled():
            return None

        with dynamo_timed(
            key="TritonBundler.read_and_emit", log_pt2_compile_event=True
        ):
            kernel_names: list[str] = []

            for artifacts in bundle.kernel_artifacts:
                basedir = triton_cache_dir(artifacts.device)
                directory = os.path.join(basedir, artifacts.kernel_hash)

                if os.path.exists(directory) and len(os.listdir(directory)) != 0:
                    # If directory already exists, we bail out and leave
                    # local disk to take care of caching
                    log.debug(
                        "Bailing out TritonBundler.read_and_emit, %s is non empty",
                        directory,
                    )
                    continue

                Path(basedir).mkdir(parents=True, exist_ok=True)

                # Random ID to avoid any collisions
                rnd_id = str(uuid.uuid4())
                tmp_dir = os.path.join(basedir, f"tmp.{rnd_id}")
                os.makedirs(tmp_dir)

                for artifact in artifacts.artifacts:
                    filepath = os.path.join(tmp_dir, artifact.filename)
                    with open(filepath, "wb") as file:
                        payload = artifact.payload
                        if artifact.filename.endswith(".json"):
                            payload = payload.replace(
                                TritonBundler._REPLACE_BYTES, str.encode(directory)
                            )
                        file.write(payload)
                    counters["inductor"]["triton_bundler_read_and_emit_kernel"] += 1
                    extension = os.path.splitext(artifact.filename)[1]
                    if extension in GPU_KERNEL_BIN_EXTS.values():
                        # Each kernel has bunch of files like .cubin(for cuda), zebin(for xpu), .json, .ttir
                        # Just append one of them without the extension
                        kernel_names.append(Path(artifact.filename).stem)

                if _IS_WINDOWS:
                    with FileLock(directory + ".lock"):
                        if os.path.exists(directory):
                            shutil.rmtree(directory)
                        os.replace(tmp_dir, directory)
                else:
                    # Atomic on POSIX systems
                    try:
                        os.replace(tmp_dir, directory)
                    except OSError:
                        log.warning("Directory %s is not empty - skipping!", tmp_dir)

            if config.use_static_triton_launcher:
                static_kernel_names = TritonBundler.load_autotuners(
                    bundle.static_autotuners
                )
            else:
                static_kernel_names = []
            return TritonBundlerMetadata(kernel_names, static_kernel_names)