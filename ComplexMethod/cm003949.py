def convert_wav2vec2_checkpoint(
    checkpoint_path, pytorch_dump_folder_path, config_path=None, dict_path=None, is_finetuned=True
):
    """
    Copy/paste/tweak model's weights to transformers design.
    """
    if config_path is not None:
        config = Data2VecAudioConfig.from_pretrained(config_path)
    else:
        config = Data2VecAudioConfig()

    if not is_finetuned:
        # Modify final_proj layer name
        hf_wav2vec = Data2VecAudioModel(config)
        data2vec_checkpoint_dir = os.path.dirname(checkpoint_path)

        state_dict = torch.load(checkpoint_path, weights_only=True)
        state_dict["model"]["final_proj.weight"] = state_dict["model"].pop("final_proj.0.weight")
        state_dict["model"]["final_proj.bias"] = state_dict["model"].pop("final_proj.0.bias")
        converted_ckpt = os.path.join(data2vec_checkpoint_dir, "converted.pt")
        torch.save(state_dict, converted_ckpt)
    else:
        hf_wav2vec = Data2VecAudioForCTC(config)
        converted_ckpt = checkpoint_path

    def load_data2vec(path):
        model, _, _ = fairseq.checkpoint_utils.load_model_ensemble_and_task([path])
        return model[0].eval()

    model = load_data2vec(converted_ckpt)

    recursively_load_weights(model, hf_wav2vec, not is_finetuned)

    processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-large-lv60")

    ds = load_dataset("hf-internal-testing/librispeech_asr_dummy", "clean", split="validation")
    input_audio = [x["array"] for x in ds[:4]["audio"]]

    inputs = processor(input_audio, return_tensors="pt", padding=True)

    input_values = inputs.input_values
    attention_mask = inputs.attention_mask
    #    input_values = inputs.input_values[:, :-1]
    #    attention_mask = inputs.attention_mask[:, :-1]

    hf_wav2vec.eval()
    model.eval()
    if is_finetuned:
        their_output = model(source=input_values, padding_mask=(1 - attention_mask), mask=False, features_only=True)[
            "encoder_out"
        ].transpose(0, 1)
        our_output = hf_wav2vec(input_values, attention_mask=attention_mask)["logits"]

        pred_ids = torch.argmax(our_output, dim=-1)
        output_string = processor.batch_decode(pred_ids)

        print(f"Expected Output: {ds[:4]['text']}, Pred: {output_string}")
    else:
        their_output = model(source=input_values, padding_mask=(1 - attention_mask), mask=False, features_only=True)[
            "layer_results"
        ][-1][0].transpose(0, 1)
        our_output = hf_wav2vec(input_values, attention_mask=attention_mask)["last_hidden_state"]

    print(our_output.shape, their_output.shape)
    max_absolute_diff = torch.max(torch.abs(our_output - their_output)).item()
    print(f"max_absolute_diff = {max_absolute_diff}")  # ~ 1e-7
    success = torch.allclose(our_output, their_output, atol=1e-3)
    print("Do both models output the same tensors?", "[PASS]" if success else "[FAIL]")
    if not success:
        raise Exception("Something went wRoNg")

    hf_wav2vec.save_pretrained(pytorch_dump_folder_path)

    if is_finetuned:
        processor.save_pretrained(pytorch_dump_folder_path)
    else:
        processor.feature_extractor.save_pretrained(pytorch_dump_folder_path)