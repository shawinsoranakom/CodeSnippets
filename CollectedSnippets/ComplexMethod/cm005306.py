def rename_keys(state_dict, architecture):
    for name in list(state_dict):
        param = state_dict.pop(name)

        # PREPROCESSORS
        # rename text preprocessor embeddings (for MLM model)
        name = name.replace("embed/embeddings", "input_preprocessor.embeddings.weight")
        if name.startswith("trainable_position_encoding/pos_embs"):
            name = name.replace(
                "trainable_position_encoding/pos_embs", "input_preprocessor.position_embeddings.weight"
            )

        # rename image preprocessor embeddings (for image classification model with learned position embeddings)
        name = name.replace("image_preprocessor/~/conv2_d/w", "input_preprocessor.convnet_1x1.weight")
        name = name.replace("image_preprocessor/~/conv2_d/b", "input_preprocessor.convnet_1x1.bias")
        name = name.replace(
            "image_preprocessor/~_build_network_inputs/trainable_position_encoding/pos_embs",
            "input_preprocessor.position_embeddings.position_embeddings",
        )
        name = name.replace(
            "image_preprocessor/~_build_network_inputs/position_encoding_projector/linear/w",
            "input_preprocessor.positions_projection.weight",
        )
        name = name.replace(
            "image_preprocessor/~_build_network_inputs/position_encoding_projector/linear/b",
            "input_preprocessor.positions_projection.bias",
        )

        # rename image preprocessor embeddings (for image classification model with conv processing)
        if "counter" in name or "hidden" in name:
            continue
        name = name.replace(
            "image_preprocessor/~/conv2_d_downsample/~/conv/w", "input_preprocessor.convnet.conv.weight"
        )
        name = name.replace(
            "image_preprocessor/~/conv2_d_downsample/~/batchnorm/offset", "input_preprocessor.convnet.batchnorm.bias"
        )
        name = name.replace(
            "image_preprocessor/~/conv2_d_downsample/~/batchnorm/scale", "input_preprocessor.convnet.batchnorm.weight"
        )
        name = name.replace(
            "image_preprocessor/~/conv2_d_downsample/~/batchnorm/~/mean_ema/average",
            "input_preprocessor.convnet.batchnorm.running_mean",
        )
        name = name.replace(
            "image_preprocessor/~/conv2_d_downsample/~/batchnorm/~/var_ema/average",
            "input_preprocessor.convnet.batchnorm.running_var",
        )

        # rename image preprocessor embeddings (for optical flow model)
        name = name.replace("image_preprocessor/patches_linear/b", "input_preprocessor.conv_after_patches.bias")
        name = name.replace("image_preprocessor/patches_linear/w", "input_preprocessor.conv_after_patches.weight")

        # rename multimodal preprocessor embeddings
        name = name.replace("multimodal_preprocessor/audio_mask_token/pos_embs", "input_preprocessor.mask.audio")
        name = name.replace("multimodal_preprocessor/audio_padding/pos_embs", "input_preprocessor.padding.audio")
        name = name.replace("multimodal_preprocessor/image_mask_token/pos_embs", "input_preprocessor.mask.image")
        name = name.replace("multimodal_preprocessor/image_padding/pos_embs", "input_preprocessor.padding.image")
        name = name.replace("multimodal_preprocessor/label_mask_token/pos_embs", "input_preprocessor.mask.label")
        name = name.replace("multimodal_preprocessor/label_padding/pos_embs", "input_preprocessor.padding.label")

        # DECODERS
        # rename prefix of decoders
        # multimodal autoencoding model
        name = name.replace(
            "multimodal_decoder/~/basic_decoder/cross_attention/", "decoder.decoder.decoding_cross_attention."
        )
        name = name.replace("multimodal_decoder/~decoder_query/audio_padding/pos_embs", "decoder.padding.audio")
        name = name.replace("multimodal_decoder/~decoder_query/image_padding/pos_embs", "decoder.padding.image")
        name = name.replace("multimodal_decoder/~decoder_query/label_padding/pos_embs", "decoder.padding.label")
        name = name.replace("multimodal_decoder/~/basic_decoder/output/b", "decoder.decoder.final_layer.bias")
        name = name.replace("multimodal_decoder/~/basic_decoder/output/w", "decoder.decoder.final_layer.weight")
        if architecture == "multimodal_autoencoding":
            name = name.replace(
                "classification_decoder/~/basic_decoder/~/trainable_position_encoding/pos_embs",
                "decoder.modalities.label.decoder.output_position_encodings.position_embeddings",
            )
        # flow model
        name = name.replace(
            "flow_decoder/~/basic_decoder/cross_attention/", "decoder.decoder.decoding_cross_attention."
        )
        name = name.replace("flow_decoder/~/basic_decoder/output/w", "decoder.decoder.final_layer.weight")
        name = name.replace("flow_decoder/~/basic_decoder/output/b", "decoder.decoder.final_layer.bias")
        # image models
        name = name.replace(
            "classification_decoder/~/basic_decoder/~/trainable_position_encoding/pos_embs",
            "decoder.decoder.output_position_encodings.position_embeddings",
        )
        name = name.replace(
            "basic_decoder/~/trainable_position_encoding/pos_embs",
            "decoder.output_position_encodings.position_embeddings",
        )
        name = name.replace(
            "classification_decoder/~/basic_decoder/cross_attention/", "decoder.decoder.decoding_cross_attention."
        )
        name = name.replace("classification_decoder/~/basic_decoder/output/b", "decoder.decoder.final_layer.bias")
        name = name.replace("classification_decoder/~/basic_decoder/output/w", "decoder.decoder.final_layer.weight")
        name = name.replace("classification_decoder/~/basic_decoder/~/", "decoder.decoder.")
        name = name.replace("basic_decoder/cross_attention/", "decoder.decoding_cross_attention.")
        name = name.replace("basic_decoder/~/", "decoder.")

        # POSTPROCESSORS
        name = name.replace(
            "projection_postprocessor/linear/b", "output_postprocessor.modalities.image.classifier.bias"
        )
        name = name.replace(
            "projection_postprocessor/linear/w", "output_postprocessor.modalities.image.classifier.weight"
        )
        name = name.replace(
            "classification_postprocessor/linear/b", "output_postprocessor.modalities.label.classifier.bias"
        )
        name = name.replace(
            "classification_postprocessor/linear/w", "output_postprocessor.modalities.label.classifier.weight"
        )
        name = name.replace("audio_postprocessor/linear/b", "output_postprocessor.modalities.audio.classifier.bias")
        name = name.replace("audio_postprocessor/linear/w", "output_postprocessor.modalities.audio.classifier.weight")

        # PERCEIVER MODEL

        # rename latent embeddings
        name = name.replace("perceiver_encoder/~/trainable_position_encoding/pos_embs", "embeddings.latents")
        # rename latent embeddings (for multimodal model)
        name = name.replace("encoder/~/trainable_position_encoding/pos_embs", "embeddings.latents")

        # rename prefixes
        if name.startswith("perceiver_encoder/~/"):
            if "self_attention" in name:
                suffix = "self_attends."
            else:
                suffix = ""
            name = name.replace("perceiver_encoder/~/", "encoder." + suffix)
        if name.startswith("encoder/~/"):
            if "self_attention" in name:
                suffix = "self_attends."
            else:
                suffix = ""
            name = name.replace("encoder/~/", "encoder." + suffix)
        # rename layernorm parameters
        if "offset" in name:
            name = name.replace("offset", "bias")
        if "scale" in name:
            name = name.replace("scale", "weight")
        # in HuggingFace, the layernorm in between attention + MLP is just called "layernorm"
        # rename layernorm in between attention + MLP of cross-attention
        if "cross_attention" in name and "layer_norm_2" in name:
            name = name.replace("layer_norm_2", "layernorm")
        # rename layernorm in between attention + MLP of self-attention
        if "self_attention" in name and "layer_norm_1" in name:
            name = name.replace("layer_norm_1", "layernorm")

        # in HuggingFace, the layernorms for queries + keys are called "layernorm1" and "layernorm2"
        if "cross_attention" in name and "layer_norm_1" in name:
            name = name.replace("layer_norm_1", "attention.self.layernorm2")
        if "cross_attention" in name and "layer_norm" in name:
            name = name.replace("layer_norm", "attention.self.layernorm1")
        if "self_attention" in name and "layer_norm" in name:
            name = name.replace("layer_norm", "attention.self.layernorm1")

        # rename special characters by dots
        name = name.replace("-", ".")
        name = name.replace("/", ".")
        # rename keys, queries, values and output of attention layers
        if ("cross_attention" in name or "self_attention" in name) and "mlp" not in name:
            if "linear.b" in name:
                name = name.replace("linear.b", "self.query.bias")
            if "linear.w" in name:
                name = name.replace("linear.w", "self.query.weight")
            if "linear_1.b" in name:
                name = name.replace("linear_1.b", "self.key.bias")
            if "linear_1.w" in name:
                name = name.replace("linear_1.w", "self.key.weight")
            if "linear_2.b" in name:
                name = name.replace("linear_2.b", "self.value.bias")
            if "linear_2.w" in name:
                name = name.replace("linear_2.w", "self.value.weight")
            if "linear_3.b" in name:
                name = name.replace("linear_3.b", "output.dense.bias")
            if "linear_3.w" in name:
                name = name.replace("linear_3.w", "output.dense.weight")
        if "self_attention_" in name:
            name = name.replace("self_attention_", "")
        if "self_attention" in name:
            name = name.replace("self_attention", "0")
        # rename dense layers of 2-layer MLP
        if "mlp" in name:
            if "linear.b" in name:
                name = name.replace("linear.b", "dense1.bias")
            if "linear.w" in name:
                name = name.replace("linear.w", "dense1.weight")
            if "linear_1.b" in name:
                name = name.replace("linear_1.b", "dense2.bias")
            if "linear_1.w" in name:
                name = name.replace("linear_1.w", "dense2.weight")

        # finally, TRANSPOSE if kernel and not embedding layer, and set value
        if name[-6:] == "weight" and "embeddings" not in name:
            param = np.transpose(param)

        # if batchnorm, we need to squeeze it
        if "batchnorm" in name:
            param = np.squeeze(param)

        if "embedding_decoder" not in name:
            state_dict["perceiver." + name] = torch.from_numpy(param)
        else:
            state_dict[name] = torch.from_numpy(param)