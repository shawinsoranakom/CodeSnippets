def _load_pretrained_weights(self):
        """
        ### Load pre-trained [GPT-2 from huggingface](https://huggingface.co/openai-community/gpt2)
        """

        # Load the huggingface model and get the parameters
        hf_model = AutoModelForCausalLM.from_pretrained("gpt2")
        state_dict = hf_model.state_dict()

        # Transformer embedding and prediction layer parameter mapping (`hf: ours`)
        mapping = {
            'transformer.wte.weight': 'token_embedding.weight',
            'transformer.wpe.weight': 'position_embedding.weight',
            'transformer.ln_f.weight': 'final_norm.weight',
            'transformer.ln_f.bias': 'final_norm.bias',
            'lm_head.weight': 'lm_head.weight'
        }

        # Mapping (`hf: ours`) of decoder layers
        for i in range(12):
            mapping[f'transformer.h.{i}.ln_1.weight'] = f'blocks.{i}.attn_norm.weight'
            mapping[f'transformer.h.{i}.ln_1.bias'] = f'blocks.{i}.attn_norm.bias'
            mapping[f'transformer.h.{i}.attn.c_attn.weight'] = f'blocks.{i}.attn.qkv_projection.weight'
            mapping[f'transformer.h.{i}.attn.c_attn.bias'] = f'blocks.{i}.attn.qkv_projection.bias'
            mapping[f'transformer.h.{i}.attn.c_proj.weight'] = f'blocks.{i}.attn.output_projection.weight'
            mapping[f'transformer.h.{i}.attn.c_proj.bias'] = f'blocks.{i}.attn.output_projection.bias'
            mapping[f'transformer.h.{i}.ln_2.weight'] = f'blocks.{i}.ffn_norm.weight'
            mapping[f'transformer.h.{i}.ln_2.bias'] = f'blocks.{i}.ffn_norm.bias'
            mapping[f'transformer.h.{i}.mlp.c_fc.weight'] = f'blocks.{i}.ffn.linear_in.weight'
            mapping[f'transformer.h.{i}.mlp.c_fc.bias'] = f'blocks.{i}.ffn.linear_in.bias'
            mapping[f'transformer.h.{i}.mlp.c_proj.weight'] = f'blocks.{i}.ffn.linear_out.weight'
            mapping[f'transformer.h.{i}.mlp.c_proj.bias'] = f'blocks.{i}.ffn.linear_out.bias'

        # Move the parameters based on mapping
        new_state_dict = {}
        for old_key, new_key in mapping.items():
            if old_key in state_dict:
                new_state_dict[new_key] = state_dict[old_key]

        # GPT-2 hugging face uses 1D Convolution layers. We need to transpose those weights since we use linear layers
        convo_layers = ([f'blocks.{i}.ffn.linear_in.weight' for i in range(12)] +
                        [f'blocks.{i}.ffn.linear_out.weight' for i in range(12)] +
                        [f'blocks.{i}.attn.qkv_projection.weight' for i in range(12)] +
                        [f'blocks.{i}.attn.output_projection.weight' for i in range(12)])

        for layer in convo_layers:
            new_state_dict[layer] = torch.transpose(new_state_dict[layer], 0, 1)

        # Load out model. We use `strict = False` because the state does not have LoRA weights
        missing_keys, unexpected_keys = self.model.load_state_dict(new_state_dict, strict=False)

        # make sure that only lora weights are not loaded
        assert all('lora' in key for key in missing_keys)
        assert not unexpected_keys