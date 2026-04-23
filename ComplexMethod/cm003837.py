def rename_keys(original_param_names):
    # EfficientNet image encoder
    block_names = [v.split("_")[0].split("block")[1] for v in original_param_names if v.startswith("block")]
    block_names = list(set(block_names))
    block_names = sorted(block_names)
    num_blocks = len(block_names)
    block_name_mapping = {b: str(i) for b, i in zip(block_names, range(num_blocks))}

    rename_keys = []
    rename_keys.append(("stem_conv/kernel:0", "embeddings.convolution.weight"))
    rename_keys.append(("stem_bn/gamma:0", "embeddings.batchnorm.weight"))
    rename_keys.append(("stem_bn/beta:0", "embeddings.batchnorm.bias"))
    rename_keys.append(("stem_bn/moving_mean:0", "embeddings.batchnorm.running_mean"))
    rename_keys.append(("stem_bn/moving_variance:0", "embeddings.batchnorm.running_var"))

    for b in block_names:
        hf_b = block_name_mapping[b]
        rename_keys.append((f"block{b}_expand_conv/kernel:0", f"encoder.blocks.{hf_b}.expansion.expand_conv.weight"))
        rename_keys.append((f"block{b}_expand_bn/gamma:0", f"encoder.blocks.{hf_b}.expansion.expand_bn.weight"))
        rename_keys.append((f"block{b}_expand_bn/beta:0", f"encoder.blocks.{hf_b}.expansion.expand_bn.bias"))
        rename_keys.append(
            (f"block{b}_expand_bn/moving_mean:0", f"encoder.blocks.{hf_b}.expansion.expand_bn.running_mean")
        )
        rename_keys.append(
            (f"block{b}_expand_bn/moving_variance:0", f"encoder.blocks.{hf_b}.expansion.expand_bn.running_var")
        )
        rename_keys.append(
            (f"block{b}_dwconv/depthwise_kernel:0", f"encoder.blocks.{hf_b}.depthwise_conv.depthwise_conv.weight")
        )
        rename_keys.append((f"block{b}_bn/gamma:0", f"encoder.blocks.{hf_b}.depthwise_conv.depthwise_norm.weight"))
        rename_keys.append((f"block{b}_bn/beta:0", f"encoder.blocks.{hf_b}.depthwise_conv.depthwise_norm.bias"))
        rename_keys.append(
            (f"block{b}_bn/moving_mean:0", f"encoder.blocks.{hf_b}.depthwise_conv.depthwise_norm.running_mean")
        )
        rename_keys.append(
            (f"block{b}_bn/moving_variance:0", f"encoder.blocks.{hf_b}.depthwise_conv.depthwise_norm.running_var")
        )

        rename_keys.append((f"block{b}_se_reduce/kernel:0", f"encoder.blocks.{hf_b}.squeeze_excite.reduce.weight"))
        rename_keys.append((f"block{b}_se_reduce/bias:0", f"encoder.blocks.{hf_b}.squeeze_excite.reduce.bias"))
        rename_keys.append((f"block{b}_se_expand/kernel:0", f"encoder.blocks.{hf_b}.squeeze_excite.expand.weight"))
        rename_keys.append((f"block{b}_se_expand/bias:0", f"encoder.blocks.{hf_b}.squeeze_excite.expand.bias"))
        rename_keys.append(
            (f"block{b}_project_conv/kernel:0", f"encoder.blocks.{hf_b}.projection.project_conv.weight")
        )
        rename_keys.append((f"block{b}_project_bn/gamma:0", f"encoder.blocks.{hf_b}.projection.project_bn.weight"))
        rename_keys.append((f"block{b}_project_bn/beta:0", f"encoder.blocks.{hf_b}.projection.project_bn.bias"))
        rename_keys.append(
            (f"block{b}_project_bn/moving_mean:0", f"encoder.blocks.{hf_b}.projection.project_bn.running_mean")
        )
        rename_keys.append(
            (f"block{b}_project_bn/moving_variance:0", f"encoder.blocks.{hf_b}.projection.project_bn.running_var")
        )

    key_mapping = {}
    for item in rename_keys:
        if item[0] in original_param_names:
            key_mapping[item[0]] = "vision_model." + item[1]

    # BERT text encoder
    rename_keys = []
    old = "tf_bert_model/bert"
    new = "text_model"
    for i in range(12):
        rename_keys.append(
            (
                f"{old}/encoder/layer_._{i}/attention/self/query/kernel:0",
                f"{new}.encoder.layer.{i}.attention.self.query.weight",
            )
        )
        rename_keys.append(
            (
                f"{old}/encoder/layer_._{i}/attention/self/query/bias:0",
                f"{new}.encoder.layer.{i}.attention.self.query.bias",
            )
        )
        rename_keys.append(
            (
                f"{old}/encoder/layer_._{i}/attention/self/key/kernel:0",
                f"{new}.encoder.layer.{i}.attention.self.key.weight",
            )
        )
        rename_keys.append(
            (
                f"{old}/encoder/layer_._{i}/attention/self/key/bias:0",
                f"{new}.encoder.layer.{i}.attention.self.key.bias",
            )
        )
        rename_keys.append(
            (
                f"{old}/encoder/layer_._{i}/attention/self/value/kernel:0",
                f"{new}.encoder.layer.{i}.attention.self.value.weight",
            )
        )
        rename_keys.append(
            (
                f"{old}/encoder/layer_._{i}/attention/self/value/bias:0",
                f"{new}.encoder.layer.{i}.attention.self.value.bias",
            )
        )
        rename_keys.append(
            (
                f"{old}/encoder/layer_._{i}/attention/output/dense/kernel:0",
                f"{new}.encoder.layer.{i}.attention.output.dense.weight",
            )
        )
        rename_keys.append(
            (
                f"{old}/encoder/layer_._{i}/attention/output/dense/bias:0",
                f"{new}.encoder.layer.{i}.attention.output.dense.bias",
            )
        )
        rename_keys.append(
            (
                f"{old}/encoder/layer_._{i}/attention/output/LayerNorm/gamma:0",
                f"{new}.encoder.layer.{i}.attention.output.LayerNorm.weight",
            )
        )
        rename_keys.append(
            (
                f"{old}/encoder/layer_._{i}/attention/output/LayerNorm/beta:0",
                f"{new}.encoder.layer.{i}.attention.output.LayerNorm.bias",
            )
        )
        rename_keys.append(
            (
                f"{old}/encoder/layer_._{i}/intermediate/dense/kernel:0",
                f"{new}.encoder.layer.{i}.intermediate.dense.weight",
            )
        )
        rename_keys.append(
            (
                f"{old}/encoder/layer_._{i}/intermediate/dense/bias:0",
                f"{new}.encoder.layer.{i}.intermediate.dense.bias",
            )
        )
        rename_keys.append(
            (f"{old}/encoder/layer_._{i}/output/dense/kernel:0", f"{new}.encoder.layer.{i}.output.dense.weight")
        )
        rename_keys.append(
            (f"{old}/encoder/layer_._{i}/output/dense/bias:0", f"{new}.encoder.layer.{i}.output.dense.bias")
        )
        rename_keys.append(
            (f"{old}/encoder/layer_._{i}/output/LayerNorm/gamma:0", f"{new}.encoder.layer.{i}.output.LayerNorm.weight")
        )
        rename_keys.append(
            (f"{old}/encoder/layer_._{i}/output/LayerNorm/beta:0", f"{new}.encoder.layer.{i}.output.LayerNorm.bias")
        )

    rename_keys.append((f"{old}/embeddings/word_embeddings/weight:0", f"{new}.embeddings.word_embeddings.weight"))
    rename_keys.append(
        (f"{old}/embeddings/position_embeddings/embeddings:0", f"{new}.embeddings.position_embeddings.weight")
    )
    rename_keys.append(
        (f"{old}/embeddings/token_type_embeddings/embeddings:0", f"{new}.embeddings.token_type_embeddings.weight")
    )
    rename_keys.append((f"{old}/embeddings/LayerNorm/gamma:0", f"{new}.embeddings.LayerNorm.weight"))
    rename_keys.append((f"{old}/embeddings/LayerNorm/beta:0", f"{new}.embeddings.LayerNorm.bias"))

    rename_keys.append((f"{old}/pooler/dense/kernel:0", f"{new}.pooler.dense.weight"))
    rename_keys.append((f"{old}/pooler/dense/bias:0", f"{new}.pooler.dense.bias"))
    rename_keys.append(("dense/kernel:0", "text_projection.weight"))
    rename_keys.append(("dense/bias:0", "text_projection.bias"))
    rename_keys.append(("dense/bias:0", "text_projection.bias"))
    rename_keys.append(("temperature:0", "temperature"))

    for item in rename_keys:
        if item[0] in original_param_names:
            key_mapping[item[0]] = item[1]
    return key_mapping