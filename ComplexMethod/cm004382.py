def main():
    # Create the argument parser.
    parser = argparse.ArgumentParser()
    parser.add_argument("--print-checkpoint-structure", action="store_true")
    parser.add_argument(
        "path_to_checkpoint",
        type=str,
        help="Path to the checkpoint file (.zip archive or direct .pt file)",
    )
    parser.add_argument(
        "--config_file",
        default="",
        type=str,
        help="An optional config json file describing the pre-trained model.",
    )
    args = parser.parse_args()

    # Extract the basename.
    basename = os.path.dirname(args.path_to_checkpoint)

    # Load the model.
    # the .zip is very optional, let's keep it for backward compatibility
    print(f"Extracting PyTorch state dictionary from {args.path_to_checkpoint}")
    if args.path_to_checkpoint.endswith(".zip"):
        with zipfile.ZipFile(args.path_to_checkpoint, "r") as checkpoint:
            with checkpoint.open("release/mp_rank_00/model_optim_rng.pt") as pytorch_dict:
                input_state_dict = torch.load(pytorch_dict, map_location="cpu", weights_only=True)
    else:
        input_state_dict = torch.load(args.path_to_checkpoint, map_location="cpu", weights_only=False)

    ds_args = input_state_dict.get("args", None)

    # Read the config, or default to the model released by NVIDIA.
    if args.config_file == "":
        if ds_args is not None:
            if ds_args.bias_gelu_fusion:
                activation_function = "gelu_fast"
            elif ds_args.openai_gelu:
                activation_function = "gelu_new"
            else:
                activation_function = "gelu"
        else:
            # in the very early days this used to be "gelu_new"
            activation_function = "gelu_new"

        # Spell out all parameters in case the defaults change.
        config = GPT2Config(
            vocab_size=50257,
            n_positions=1024,
            n_embd=1024,
            n_layer=24,
            n_head=16,
            n_inner=4096,
            activation_function=activation_function,
            resid_pdrop=0.1,
            embd_pdrop=0.1,
            attn_pdrop=0.1,
            layer_norm_epsilon=1e-5,
            initializer_range=0.02,
            summary_type="cls_index",
            summary_use_proj=True,
            summary_activation=None,
            summary_proj_to_labels=True,
            summary_first_dropout=0.1,
            scale_attn_weights=True,
            use_cache=True,
            bos_token_id=50256,
            eos_token_id=50256,
        )
    else:
        config = GPT2Config.from_json_file(args.config_file)

    config.architectures = ["GPT2LMHeadModel"]

    # Convert.
    print("Converting")
    output_state_dict = convert_megatron_checkpoint(args, input_state_dict, config)

    # Print the structure of converted state dict.
    if args.print_checkpoint_structure:
        recursive_print(None, output_state_dict)

    # Add tokenizer class info to config
    # see https://github.com/huggingface/transformers/issues/13906)
    if ds_args is not None:
        tokenizer_type = ds_args.tokenizer_type
        if tokenizer_type == "GPT2BPETokenizer":
            tokenizer_model_name = "openai-community/gpt2"
        elif tokenizer_type == "PretrainedFromHF":
            tokenizer_model_name = ds_args.tokenizer_name_or_path
        else:
            raise ValueError(f"Unrecognized tokenizer_type {tokenizer_type}")
    else:
        tokenizer_model_name = "openai-community/gpt2"

    tokenizer = AutoTokenizer.from_pretrained(tokenizer_model_name)
    tokenizer_class = type(tokenizer).__name__
    config.tokenizer_class = tokenizer_class

    # Store the config to file.
    print("Saving config")
    config.save_pretrained(basename)

    # Save tokenizer based on args
    print(f"Adding {tokenizer_class} tokenizer files")
    tokenizer.save_pretrained(basename)

    # Store the state_dict to file.
    output_checkpoint_file = os.path.join(basename, "pytorch_model.bin")
    print(f'Saving checkpoint to "{output_checkpoint_file}"')
    torch.save(output_state_dict, output_checkpoint_file)