def unsloth_convert_lora_to_ggml_and_save_locally(
    self,
    save_directory: str,  # Added parameter for the folder name
    tokenizer,
    temporary_location: str = "_unsloth_temporary_saved_buffers",
    maximum_memory_usage: float = 0.85,
):
    if not os.path.exists("llama.cpp"):
        if IS_KAGGLE_ENVIRONMENT:
            python_install = install_python_non_blocking(["protobuf"])
            python_install.wait()
            install_llama_cpp_blocking(use_cuda = False)
            makefile = None
        else:
            git_clone = install_llama_cpp_clone_non_blocking()
            python_install = install_python_non_blocking(["protobuf"])
            git_clone.wait()
            makefile = install_llama_cpp_make_non_blocking()
            python_install.wait()
    else:
        makefile = None

    for _ in range(3):
        gc.collect()

    # Use the provided save_directory for local saving
    save_lora_to_custom_dir(self, tokenizer, save_directory)

    model_type = self.config.model_type
    output_file = os.path.join(save_directory, "ggml-adapter-model.bin")

    print(
        f"Unsloth: Converting auto-saved LoRA adapters at {save_directory} to GGML format."
    )
    print(f"The output file will be {output_file}")

    try:
        with subprocess.Popen(
            [
                sys.executable,
                "llama.cpp/convert-lora-to-ggml.py",
                save_directory,
                output_file,
                "llama",
            ],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            bufsize = 1,
            universal_newlines = True,
        ) as sp:
            for line in sp.stdout:
                print(line, end = "", flush = True)
            for line in sp.stderr:
                print(line, end = "", flush = True)
            sp.wait()
            if sp.returncode != 0:
                raise subprocess.CalledProcessError(sp.returncode, sp.args)
    except subprocess.CalledProcessError as e:
        print(f"Error: Conversion failed with return code {e.returncode}")
        return
    print("Unsloth: Done.")
    print(f"Unsloth: Conversion completed! Output file: {output_file}")
    print(
        "\nThis GGML making function was made by Maheswar. Ping him @Maheswar on the Unsloth Discord or on HuggingFace (@mahiatlinux) if you like this!"
    )