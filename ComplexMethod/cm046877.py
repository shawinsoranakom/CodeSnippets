def save_to_gguf(
    model_name: str,
    model_type: str,
    model_dtype: str,
    is_sentencepiece: bool = False,
    model_directory: str = "unsloth_finetuned_model",
    quantization_method = "fast_quantized",  # Can be a list of options! ["q4_k_m", "q8_0", "q5_k_m"]
    first_conversion: str = None,
    is_vlm: bool = False,
    is_gpt_oss: bool = False,
):
    """
    Orchestrates the complete GGUF conversion process.
    Handles installation, conversion, and quantization.
    """
    # print_output True only if UNSLOTH_ENABLE_LOGGING=1
    if os.environ.get("UNSLOTH_ENABLE_LOGGING", "0") == "1":
        print_output = True
    else:
        print_output = False

    # Validate model dtype
    assert model_dtype == "float16" or model_dtype == "bfloat16"
    model_dtype = "f16" if model_dtype == "float16" else "bf16"

    # Convert quantization_method to list
    if isinstance(quantization_method, list):
        pass
    elif isinstance(quantization_method, str):
        quantization_method = [
            quantization_method,
        ]
    elif isinstance(quantization_method, tuple):
        quantization_method = list(quantization_method)
    else:
        raise TypeError(
            "Unsloth: quantization_method can only be a string or a list of strings"
        )

    # Check if bfloat16 is supported
    if model_dtype == "bf16" and not torch.cuda.is_bf16_supported():
        logger.warning(
            "Unsloth: Cannot convert to bf16 GGUF since your computer doesn't support it.\n"
            "We shall switch instead to f16."
        )
        model_dtype = "f16"

    # Check first_conversion as well
    if first_conversion is None:
        first_conversion = model_dtype

    # Check I quants
    for quant_method in quantization_method:
        if quant_method.startswith("iq2"):
            raise RuntimeError(
                "Unsloth: Currently iq2 type quantizations aren't supported yet - sorry!"
            )

    # Map quant methods
    new_quantization_methods = []
    for quant_method in quantization_method:
        if quant_method == "not_quantized":
            quant_method = model_dtype
        elif quant_method == "fast_quantized":
            quant_method = "q8_0"
        elif quant_method == "quantized":
            quant_method = "q4_k_m"
        elif quant_method is None:
            quant_method = "q8_0"

        # Check if wrong method
        if quant_method not in ALLOWED_QUANTS.keys():
            error = f"Unsloth: Quant method = [{quant_method}] not supported. Choose from below:\n"
            for key, value in ALLOWED_QUANTS.items():
                error += f"[{key}] => {value}\n"
            raise RuntimeError(error)

        new_quantization_methods.append(quant_method)
    quantization_method = new_quantization_methods

    # Determine optimal first_conversion
    if is_gpt_oss:
        print("Unsloth: GPT-OSS model detected - using special conversion settings")
        first_conversion = "None"  # No quantization for GPT-OSS
        # Only keep one conversion method since GPT-OSS doesn't quantize
        quantization_method = ["None"]
    else:
        if first_conversion is None:
            # Check if q8_0 is the ONLY quantization method requested
            if len(quantization_method) == 1 and quantization_method[0] == "q8_0":
                first_conversion = "None"  # Let llama-quantize do the direct conversion
            else:
                # For all other cases, choose the highest precision format
                # that can be requantized to all requested formats
                strength = 0
                for quant_method in quantization_method:
                    if quant_method == "f32":
                        strength = max(strength, 3)
                    elif quant_method == "f16":
                        strength = max(strength, 2)
                    elif quant_method == "bf16":
                        strength = max(strength, 1)
                    # Note: we don't set strength for q8_0 here since we handle it above

                if strength >= 3:
                    first_conversion = "f32"
                elif strength >= 2:
                    first_conversion = "f16"
                elif strength >= 1:
                    first_conversion = "bf16"
                else:
                    first_conversion = "bf16"  # requantizing from q8_0 disallowed in new llama.cpp default to bf16.

    # Check bfloat16 support again for first_conversion
    if first_conversion == "bf16" and not torch.cuda.is_bf16_supported():
        logger.warning("Unsloth: Switching bf16 to f16 due to hardware limitations")
        first_conversion = "f16"

    first_conversion_dtype = "" if first_conversion == "None" else first_conversion
    # Print conversion info
    print_info = (
        f"==((====))==  Unsloth: Conversion from HF to GGUF information\n"
        f"   {chr(92)}{chr(92)}   /|    [0] Installing llama.cpp might take 3 minutes.\n"
        f"O^O/ {chr(92)}_/ {chr(92)}    [1] Converting HF to GGUF {first_conversion_dtype} might take 3 minutes.\n"
        f"{chr(92)}        /    [2] Converting GGUF {first_conversion_dtype} to {quantization_method} might take 10 minutes each.\n"
        f' "-____-"     In total, you will have to wait at least 16 minutes.\n'
    )
    print(print_info)

    # Step 1: Ensure llama.cpp is installed
    try:
        quantizer_location, converter_location = check_llama_cpp()
        print("Unsloth: llama.cpp found in the system. Skipping installation.")
    except:
        print("Unsloth: Installing llama.cpp. This might take 3 minutes...")
        if IS_KAGGLE_ENVIRONMENT:
            # Kaggle: no CUDA support due to environment limitations
            quantizer_location, converter_location = install_llama_cpp(
                gpu_support = False, print_output = print_output
            )
        else:
            quantizer_location, converter_location = install_llama_cpp(
                gpu_support = False,  # GGUF conversion doesn't need CUDA
                print_output = print_output,
            )

    # Step 2: Download and patch converter script
    print("Unsloth: Preparing converter script...")
    with use_local_gguf():
        converter_path, supported_text_archs, supported_vision_archs = (
            _download_convert_hf_to_gguf()
        )

        # Step 3: Initial GGUF conversion
        print(
            f"Unsloth: [1] Converting model into {first_conversion_dtype} GGUF format."
        )
        print(f"This might take 3 minutes...")

        initial_files, is_vlm_update = convert_to_gguf(
            model_name = model_name,
            input_folder = model_directory,
            model_dtype = model_dtype,
            quantization_type = first_conversion,
            converter_location = converter_path,
            supported_text_archs = supported_text_archs,
            supported_vision_archs = supported_vision_archs,
            is_vlm = is_vlm,
            is_gpt_oss = is_gpt_oss,
            max_shard_size = "50GB",
            print_output = print_output,
        )
    # update is_vlm switch
    is_vlm = is_vlm_update
    # Check conversion success
    for file in initial_files:
        if not os.path.exists(file):
            if IS_KAGGLE_ENVIRONMENT:
                raise RuntimeError(
                    f"Unsloth: Conversion failed for {file}\n"
                    "You are in a Kaggle environment with limited disk space (20GB).\n"
                    "Try saving to /tmp for more space or use a smaller model.\n"
                    "Alternatively, save the 16bit model first, then convert manually."
                )
            else:
                raise RuntimeError(
                    f"Unsloth: Conversion failed for {file}\n"
                    "Please check disk space and try again."
                )

    # Move initial GGUF files into a dedicated _gguf directory
    gguf_directory = f"{model_directory}_gguf"
    os.makedirs(gguf_directory, exist_ok = True)
    moved_files = []
    for fpath in initial_files:
        dst = os.path.join(gguf_directory, os.path.basename(fpath))
        shutil.move(fpath, dst)
        moved_files.append(dst)
    initial_files = moved_files

    print(f"Unsloth: Initial conversion completed! Files: {initial_files}")

    # Step 4: Additional quantizations using llama-quantize
    all_saved_locations = initial_files.copy()

    # Get CPU count for quantization
    n_cpus = psutil.cpu_count()
    if n_cpus is None:
        n_cpus = 1
    n_cpus *= 2

    if not is_gpt_oss:
        base_gguf = initial_files[0]
        quants_created = False
        for quant_method in quantization_method:
            if quant_method != first_conversion:
                print(
                    f"Unsloth: [2] Converting GGUF {first_conversion_dtype} into {quant_method}. This might take 10 minutes..."
                )
                output_location = os.path.join(
                    gguf_directory, f"{model_name}.{quant_method.upper()}.gguf"
                )
                try:
                    if quant_method == "q2_k_l":
                        quantized_file = _quantize_q2_k_l(
                            input_gguf = base_gguf,
                            output_gguf = output_location,
                            quantizer_location = quantizer_location,
                            n_threads = n_cpus,
                            print_output = print_output,
                        )
                    else:
                        # Use unsloth-zoo's standard quantization for all other methods
                        quantized_file = quantize_gguf(
                            input_gguf = base_gguf,
                            output_gguf = output_location,
                            quant_type = quant_method,
                            quantizer_location = quantizer_location,
                            print_output = print_output,
                        )
                    all_saved_locations.append(quantized_file)
                    quants_created = True
                except Exception as e:
                    if IS_KAGGLE_ENVIRONMENT:
                        raise RuntimeError(
                            f"Unsloth: Quantization failed for {output_location}\n"
                            "You are in a Kaggle environment, which might be the reason this is failing.\n"
                            "Kaggle only provides 20GB of disk space in the working directory.\n"
                            "Merging to 16bit for 7b models use 16GB of space.\n"
                            "This means using `model.{save_pretrained/push_to_hub}_merged` works, but\n"
                            "`model.{save_pretrained/push_to_hub}_gguf will use too much disk space.\n"
                            "You can try saving it to the `/tmp` directory for larger disk space.\n"
                            "I suggest you to save the 16bit model first, then use manual llama.cpp conversion.\n"
                            f"Error: {e}"
                        )
                    else:
                        if IS_WINDOWS:
                            build_instructions = (
                                f'cd "{LLAMA_CPP_DEFAULT_DIR}"\n'
                                f"cmake -S . -B build -DBUILD_SHARED_LIBS=OFF\n"
                                f"cmake --build build --config Release"
                            )
                        else:
                            build_instructions = f'cd "{LLAMA_CPP_DEFAULT_DIR}" && make clean && make all -j'

                        raise RuntimeError(
                            f"Unsloth: Quantization failed for {output_location}\n"
                            "You might have to compile llama.cpp yourself, then run this again.\n"
                            "You do not need to close this Python program. Run the following commands in a new terminal:\n"
                            f'git clone --recursive https://github.com/ggerganov/llama.cpp "{LLAMA_CPP_DEFAULT_DIR}"\n'
                            f"{build_instructions}\n"
                            "Once that's done, redo the quantization.\n"
                            f"Error: {e}"
                        )
        print("Unsloth: Model files cleanup...")
        if quants_created:
            all_saved_locations.remove(base_gguf)
            Path(base_gguf).unlink(missing_ok = True)

            # flip the list to get [text_model, mmproj] order. for text models stays the same.
            all_saved_locations.reverse()
    else:
        print("Unsloth: GPT-OSS model - skipping additional quantizations")

    if is_gpt_oss:
        want_full_precision = True
    else:
        want_full_precision = first_conversion in frozenset(quantization_method)

    print(f"Unsloth: All GGUF conversions completed successfully!")
    print(f"Generated files: {all_saved_locations}")

    return all_saved_locations, want_full_precision, is_vlm