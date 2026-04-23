def detect_te_model(sd):
    if "text_model.encoder.layers.30.mlp.fc1.weight" in sd:
        return TEModel.CLIP_G
    if "text_model.encoder.layers.22.mlp.fc1.weight" in sd:
        return TEModel.CLIP_H
    if "text_model.encoder.layers.0.mlp.fc1.weight" in sd:
        return TEModel.CLIP_L
    if "model.encoder.layers.0.mixer.Wqkv.weight" in sd:
        return TEModel.JINA_CLIP_2
    if "encoder.block.23.layer.1.DenseReluDense.wi_1.weight" in sd:
        weight = sd["encoder.block.23.layer.1.DenseReluDense.wi_1.weight"]
        if weight.shape[0] == 10240:
            return TEModel.T5_XXL
        elif weight.shape[0] == 5120:
            return TEModel.T5_XL
    if 'encoder.block.23.layer.1.DenseReluDense.wi.weight' in sd:
        return TEModel.T5_XXL_OLD
    if "encoder.block.0.layer.0.SelfAttention.k.weight" in sd:
        weight = sd['encoder.block.0.layer.0.SelfAttention.k.weight']
        if weight.shape[0] == 384:
            return TEModel.BYT5_SMALL_GLYPH
        return TEModel.T5_BASE
    if 'model.layers.0.post_feedforward_layernorm.weight' in sd:
        if 'model.layers.47.self_attn.q_norm.weight' in sd:
            return TEModel.GEMMA_3_12B
        if 'model.layers.0.self_attn.q_norm.weight' in sd:
            if 'vision_model.embeddings.patch_embedding.weight' in sd:
                return TEModel.GEMMA_3_4B_VISION
            else:
                return TEModel.GEMMA_3_4B
        return TEModel.GEMMA_2_2B
    if 'model.layers.0.self_attn.k_proj.bias' in sd:
        weight = sd['model.layers.0.self_attn.k_proj.bias']
        if weight.shape[0] == 256:
            return TEModel.QWEN25_3B
        if weight.shape[0] == 512:
            return TEModel.QWEN25_7B
    if "model.language_model.layers.0.linear_attn.A_log" in sd and "model.language_model.layers.0.input_layernorm.weight" in sd:
        weight = sd['model.language_model.layers.0.input_layernorm.weight']
        if weight.shape[0] == 1024:
            return TEModel.QWEN35_08B
        if weight.shape[0] == 2560:
            return TEModel.QWEN35_4B
        if weight.shape[0] == 4096:
            return TEModel.QWEN35_9B
        if weight.shape[0] == 5120:
            return TEModel.QWEN35_27B
        return TEModel.QWEN35_2B
    if "model.layers.0.post_attention_layernorm.weight" in sd:
        weight = sd['model.layers.0.post_attention_layernorm.weight']
        if 'model.layers.0.self_attn.q_norm.weight' in sd:
            if weight.shape[0] == 2560:
                return TEModel.QWEN3_4B
            elif weight.shape[0] == 2048:
                return TEModel.QWEN3_2B
            elif weight.shape[0] == 4096:
                return TEModel.QWEN3_8B
            elif weight.shape[0] == 1024:
                return TEModel.QWEN3_06B
        if weight.shape[0] == 5120:
            if "model.layers.39.post_attention_layernorm.weight" in sd:
                return TEModel.MISTRAL3_24B
            else:
                return TEModel.MISTRAL3_24B_PRUNED_FLUX2
        if weight.shape[0] == 3072:
            return TEModel.MINISTRAL_3_3B

        return TEModel.LLAMA3_8
    return None