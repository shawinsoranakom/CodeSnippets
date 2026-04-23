def _quantize_q2_k_l(
    input_gguf: Union[str, os.PathLike],
    output_gguf: Union[str, os.PathLike],
    quantizer_location: Union[str, os.PathLike],
    n_threads: int,
    print_output: bool = True,
):
    # "Q2_K_L" is a Unsloth-side preset, not a native llama.cpp ftype. It
    # maps to the `q2_k` ftype with `--output-tensor-type q8_0` and
    # `--token-embedding-type q8_0` so the output/embedding tensors retain
    # higher precision than a plain Q2_K quant.
    command = [
        str(quantizer_location),
        "--output-tensor-type",
        "q8_0",
        "--token-embedding-type",
        "q8_0",
        str(input_gguf),
        str(output_gguf),
        "q2_k",
        str(n_threads),
    ]

    if print_output:
        print(
            "Unsloth: Quantizing as Q2_K_L preset "
            "(q2_k + --output-tensor-type q8_0 --token-embedding-type q8_0)..."
        )

    try:
        if print_output:
            with subprocess.Popen(
                command,
                shell = False,
                text = True,
                stdout = subprocess.PIPE,
                stderr = subprocess.STDOUT,
                bufsize = 1,
            ) as sp:
                assert sp.stdout is not None
                for line in sp.stdout:
                    print(line, end = "", flush = True)

                returncode = sp.wait()
                if returncode != 0:
                    raise RuntimeError(
                        f"Failed to quantize {input_gguf} to q2_k_l: process exited with code {returncode}"
                    )
        else:
            subprocess.run(
                command,
                shell = False,
                check = True,
                capture_output = True,
                text = True,
            )
    except subprocess.CalledProcessError as e:
        if print_output and hasattr(e, "stdout") and e.stdout:
            print(e.stdout)
        error_details = ""
        if hasattr(e, "stdout") and e.stdout:
            error_details += f"\nSubprocess stdout:\n{e.stdout}"
        if hasattr(e, "stderr") and e.stderr:
            error_details += f"\nSubprocess stderr:\n{e.stderr}"
        raise RuntimeError(
            f"Failed to quantize {input_gguf} to q2_k_l: {e}{error_details}"
        )

    output_path = Path(output_gguf)
    if not output_path.exists():
        raise RuntimeError(
            f"Quantization failed - output file {output_gguf} not created"
        )

    if print_output:
        file_size_bytes = output_path.stat().st_size
        file_size_gb = file_size_bytes / (1024**3)
        print(
            f"Unsloth: Successfully quantized to {output_gguf} (size: {file_size_gb:.2f}GB)"
        )
    return str(output_gguf)