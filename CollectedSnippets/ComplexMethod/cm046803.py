def test_metal_build_failure_retries_cpu_fallback(self, tmp_path: Path):
        """When cmake --build fails on Metal, the fallback should re-configure and rebuild with CPU."""
        mock_bin = tmp_path / "mock_bin"
        mock_bin.mkdir()
        calls_file = tmp_path / "cmake_calls.log"
        # cmake mock: configure always succeeds; first --build fails, rest succeed
        cmake_script = mock_bin / "cmake"
        cmake_script.write_text(
            textwrap.dedent(f"""\
            #!/bin/bash
            echo "$*" >> "{calls_file}"
            if [ "$1" = "--build" ]; then
                BUILD_COUNTER_FILE="{tmp_path}/build_counter"
                if [ ! -f "$BUILD_COUNTER_FILE" ]; then
                    echo 1 > "$BUILD_COUNTER_FILE"
                    exit 1
                fi
            fi
            exit 0
        """)
        )
        cmake_script.chmod(0o755)

        script = textwrap.dedent(f"""\
            export PATH="{mock_bin}:$PATH"
            _IS_MACOS_ARM64=true
            NVCC_PATH=""
            GPU_BACKEND=""
            CMAKE_ARGS="-DLLAMA_BUILD_TESTS=OFF"
            _TRY_METAL_CPU_FALLBACK=false
            CPU_FALLBACK_CMAKE_ARGS="$CMAKE_ARGS"
            CMAKE_GENERATOR_ARGS=""
            NCPU=2

            _BUILD_DESC="building"
            if [ "$_IS_MACOS_ARM64" = true ]; then
                _BUILD_DESC="building (Metal)"
                CMAKE_ARGS="$CMAKE_ARGS -DGGML_METAL=ON -DGGML_METAL_EMBED_LIBRARY=ON -DGGML_METAL_USE_BF16=ON -DCMAKE_INSTALL_RPATH=@loader_path -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON"
                CPU_FALLBACK_CMAKE_ARGS="$CPU_FALLBACK_CMAKE_ARGS -DGGML_METAL=OFF"
                _TRY_METAL_CPU_FALLBACK=true
            fi

            BUILD_OK=true
            _BUILD_TMP="{tmp_path}/build_tmp"
            mkdir -p "$_BUILD_TMP"

            # Configure (succeeds)
            if ! cmake $CMAKE_GENERATOR_ARGS -S "$_BUILD_TMP" -B "$_BUILD_TMP/build" $CMAKE_ARGS; then
                if [ "$_TRY_METAL_CPU_FALLBACK" = true ]; then
                    _TRY_METAL_CPU_FALLBACK=false
                    echo "CONFIGURE_FALLBACK"
                    rm -rf "$_BUILD_TMP/build"
                    cmake $CMAKE_GENERATOR_ARGS -S "$_BUILD_TMP" -B "$_BUILD_TMP/build" $CPU_FALLBACK_CMAKE_ARGS || BUILD_OK=false
                    if [ "$BUILD_OK" = true ]; then
                        _BUILD_DESC="building (CPU fallback)"
                    fi
                else
                    BUILD_OK=false
                fi
            fi

            # Build (first --build fails, triggers fallback)
            if [ "$BUILD_OK" = true ]; then
                if ! cmake --build "$_BUILD_TMP/build" --config Release --target llama-server -j"$NCPU"; then
                    if [ "$_TRY_METAL_CPU_FALLBACK" = true ]; then
                        _TRY_METAL_CPU_FALLBACK=false
                        echo "BUILD_FALLBACK_TRIGGERED"
                        rm -rf "$_BUILD_TMP/build"
                        if cmake $CMAKE_GENERATOR_ARGS -S "$_BUILD_TMP" -B "$_BUILD_TMP/build" $CPU_FALLBACK_CMAKE_ARGS; then
                            _BUILD_DESC="building (CPU fallback)"
                            cmake --build "$_BUILD_TMP/build" --config Release --target llama-server -j"$NCPU" || BUILD_OK=false
                        else
                            BUILD_OK=false
                        fi
                    else
                        BUILD_OK=false
                    fi
                fi
            fi

            echo "BUILD_OK=$BUILD_OK"
            echo "BUILD_DESC=$_BUILD_DESC"
            echo "TRY_METAL_CPU_FALLBACK=$_TRY_METAL_CPU_FALLBACK"
        """)
        output = run_bash(script)
        assert "CONFIGURE_FALLBACK" not in output, "Configure should have succeeded"
        assert "BUILD_FALLBACK_TRIGGERED" in output
        assert "BUILD_OK=true" in output
        assert "BUILD_DESC=building (CPU fallback)" in output
        assert (
            "TRY_METAL_CPU_FALLBACK=false" in output
        ), "Fallback flag should be reset to false after build fallback"

        # Verify: configure with Metal ON, build fails, re-configure with Metal OFF, rebuild
        calls = calls_file.read_text().splitlines()
        assert len(calls) >= 4, f"Expected >= 4 cmake calls, got {len(calls)}: {calls}"
        # First call: configure with Metal ON
        assert "-DGGML_METAL=ON" in calls[0]
        # Second call: build (fails)
        assert "--build" in calls[1]
        # Third call: re-configure with Metal OFF and no RPATH flags
        assert "-DGGML_METAL=OFF" in calls[2]
        assert "-DGGML_METAL=ON" not in calls[2]
        assert (
            "@loader_path" not in calls[2]
        ), f"CPU fallback should not have RPATH: {calls[2]}"
        assert (
            "-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON" not in calls[2]
        ), f"CPU fallback should not have RPATH build flag: {calls[2]}"
        assert (
            "-DLLAMA_BUILD_TESTS=OFF" in calls[2]
        ), f"CPU fallback should preserve baseline flags: {calls[2]}"
        # Fourth call: rebuild (succeeds)
        assert "--build" in calls[3]