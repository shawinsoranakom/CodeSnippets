def test_metal_cpu_fallback_triggers_on_cmake_failure(self, tmp_path: Path):
        """When cmake fails on Metal, the fallback should retry with -DGGML_METAL=OFF."""
        mock_bin = tmp_path / "mock_bin"
        mock_bin.mkdir()
        calls_file = tmp_path / "cmake_calls.log"
        # cmake that logs args and fails on first call (Metal), succeeds on second (CPU fallback)
        cmake_script = mock_bin / "cmake"
        cmake_script.write_text(
            textwrap.dedent(f"""\
            #!/bin/bash
            echo "$*" >> "{calls_file}"
            COUNTER_FILE="{tmp_path}/cmake_counter"
            if [ ! -f "$COUNTER_FILE" ]; then
                echo 1 > "$COUNTER_FILE"
                exit 1
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
            if ! cmake -S "$_BUILD_TMP" -B "$_BUILD_TMP/build" $CMAKE_ARGS; then
                if [ "$_TRY_METAL_CPU_FALLBACK" = true ]; then
                    _TRY_METAL_CPU_FALLBACK=false
                    echo "FALLBACK_TRIGGERED"
                    rm -rf "$_BUILD_TMP/build"
                    cmake -S "$_BUILD_TMP" -B "$_BUILD_TMP/build" $CPU_FALLBACK_CMAKE_ARGS || BUILD_OK=false
                    if [ "$BUILD_OK" = true ]; then
                        _BUILD_DESC="building (CPU fallback)"
                    fi
                else
                    BUILD_OK=false
                fi
            fi

            echo "BUILD_OK=$BUILD_OK"
            echo "BUILD_DESC=$_BUILD_DESC"
            echo "TRY_METAL_CPU_FALLBACK=$_TRY_METAL_CPU_FALLBACK"
        """)
        output = run_bash(script)
        assert "FALLBACK_TRIGGERED" in output
        assert "BUILD_OK=true" in output
        assert "BUILD_DESC=building (CPU fallback)" in output
        assert (
            "TRY_METAL_CPU_FALLBACK=false" in output
        ), "Fallback flag should be reset to false after configure fallback"

        # Verify cmake args: first call has Metal ON, second has Metal OFF
        calls = calls_file.read_text().splitlines()
        assert len(calls) >= 2, f"Expected >= 2 cmake calls, got {len(calls)}"
        assert (
            "-DGGML_METAL=ON" in calls[0]
        ), f"First cmake call should have Metal ON: {calls[0]}"
        assert (
            "-DGGML_METAL=OFF" in calls[1]
        ), f"Second cmake call should have Metal OFF: {calls[1]}"
        assert (
            "-DGGML_METAL=ON" not in calls[1]
        ), f"Second cmake call should NOT have Metal ON: {calls[1]}"
        assert (
            "@loader_path" not in calls[1]
        ), f"CPU fallback should not have RPATH: {calls[1]}"
        assert (
            "-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON" not in calls[1]
        ), f"CPU fallback should not have RPATH build flag: {calls[1]}"