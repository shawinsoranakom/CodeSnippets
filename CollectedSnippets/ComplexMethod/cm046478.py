def runtime_payload_health_groups(choice: AssetChoice) -> list[list[str]]:
    if choice.install_kind == "linux-cpu":
        return [
            ["libllama-common.so*"],
            ["libllama.so*"],
            ["libggml.so*"],
            ["libggml-base.so*"],
            ["libggml-cpu-*.so*"],
            ["libmtmd.so*"],
        ]
    if choice.install_kind == "linux-cuda":
        return [
            ["libllama-common.so*"],
            ["libllama.so*"],
            ["libggml.so*"],
            ["libggml-base.so*"],
            ["libggml-cpu-*.so*"],
            ["libmtmd.so*"],
            ["libggml-cuda.so*"],
        ]
    if choice.install_kind in {"macos-arm64", "macos-x64"}:
        return [
            ["libllama*.dylib"],
            ["libggml*.dylib"],
            ["libmtmd*.dylib"],
        ]
    if choice.install_kind == "linux-rocm":
        return [
            ["libllama-common.so*"],
            ["libllama.so*"],
            ["libggml.so*"],
            ["libggml-base.so*"],
            ["libggml-cpu-*.so*"],
            ["libmtmd.so*"],
            ["libggml-hip.so*"],
        ]
    if choice.install_kind == "windows-cpu":
        return [["llama.dll"]]
    if choice.install_kind == "windows-cuda":
        return [["llama.dll"], ["ggml-cuda.dll"]]
    if choice.install_kind == "windows-hip":
        return [["llama.dll"], ["*hip*.dll"]]
    return []