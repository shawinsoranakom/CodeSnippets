def generate_inputs_for_model(
    model_cls, model, model_name, bs, device, include_loss_args=False
):
    # TODO - Check if following values are representative
    num_choices = 3
    num_visual_features = 42
    seq_length = get_sequence_length(model_cls, model_name)
    vocab_size = model.config.vocab_size

    if model_name.startswith("Wav2Vec2"):
        # TODO: If we add more input_values style models, try to work this
        # into the overall control flow
        target_length = 100
        return {
            "input_values": torch.randn((bs, seq_length), device=device),
            # Added because that's what the example training script has
            "attention_mask": rand_int_tensor(device, 0, 2, (bs, seq_length)),
            "labels": rand_int_tensor(device, 0, vocab_size, (bs, target_length)),
        }

    if model_name.endswith("MultipleChoice"):
        input = rand_int_tensor(device, 0, vocab_size, (bs, num_choices, seq_length))
    elif model_name.startswith("Roberta"):
        input = rand_int_tensor(device, 0, 1, (bs, seq_length))
    else:
        input = rand_int_tensor(device, 0, vocab_size, (bs, seq_length))

    if "Bart" in model_name:
        input[:, -1] = model.config.eos_token_id

    input_dict = {"input_ids": input}

    if model_name.startswith(("T5", "M2M100", "MT5")) or model_cls in [
        BlenderbotModel,
        BlenderbotSmallModel,
        BlenderbotForConditionalGeneration,
        PegasusModel,
        MarianModel,
        MarianMTModel,
    ]:
        input_dict["decoder_input_ids"] = input

    if model_name.startswith("Lxmert"):
        visual_feat_dim, visual_pos_dim = (
            model.config.visual_feat_dim,
            model.config.visual_pos_dim,
        )
        input_dict["visual_feats"] = torch.randn(
            bs, num_visual_features, visual_feat_dim
        )
        input_dict["visual_pos"] = torch.randn(bs, num_visual_features, visual_pos_dim)

    if include_loss_args:
        if model_name.endswith("PreTraining"):
            if model_cls in [ElectraForPreTraining, LxmertForPreTraining]:
                input_dict["labels"] = rand_int_tensor(device, 0, 1, (bs, seq_length))
            else:
                label_name = (
                    "sentence_order_label"
                    if model_cls in [AlbertForPreTraining]
                    else "next_sentence_label"
                )
                input_dict["labels"] = (
                    rand_int_tensor(device, 0, vocab_size, (bs, seq_length)),
                )
                input_dict[label_name] = rand_int_tensor(device, 0, 1, (bs,))
        elif model_name.endswith("QuestionAnswering"):
            input_dict["start_positions"] = rand_int_tensor(
                device, 0, seq_length, (bs,)
            )
            input_dict["end_positions"] = rand_int_tensor(device, 0, seq_length, (bs,))
        elif model_name.endswith(
            ("MaskedLM", "HeadModel", "CausalLM", "DoubleHeadsModel")
        ):
            input_dict["labels"] = rand_int_tensor(
                device, 0, vocab_size, (bs, seq_length)
            )
        elif model_name.endswith("TokenClassification"):
            input_dict["labels"] = rand_int_tensor(
                device, 0, model.config.num_labels - 1, (bs, seq_length)
            )
        elif model_name.endswith("MultipleChoice"):
            input_dict["labels"] = rand_int_tensor(device, 0, num_choices, (bs,))
        elif model_name.endswith("SequenceClassification"):
            input_dict["labels"] = rand_int_tensor(
                device, 0, model.config.num_labels - 1, (bs,)
            )
        elif model_name.endswith("NextSentencePrediction"):
            input_dict["labels"] = rand_int_tensor(device, 0, 1, (bs,))
        elif model_name.endswith("ForConditionalGeneration"):
            input_dict["labels"] = rand_int_tensor(
                device, 0, vocab_size - 1, (bs, seq_length)
            )
        elif model_name in EXTRA_MODELS:
            input_dict["labels"] = rand_int_tensor(
                device, 0, vocab_size, (bs, seq_length)
            )
        else:
            raise NotImplementedError(
                f"Class {model_name} unsupported for training test "
            )

    return input_dict