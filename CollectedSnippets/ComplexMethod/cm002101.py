def _check_past_key_values_for_generate(self, batch_size, past_key_values, seq_length, config):
        # Raise a useful error, asking to explicitly override the method
        if not isinstance(past_key_values, Cache):
            raise ValueError("The cache is not standard! Please overwrite `_check_past_key_values_for_generate`")

        # In this case, we simply call recursively the function on both internal caches
        if isinstance(past_key_values, EncoderDecoderCache):
            self._check_past_key_values_for_generate(
                batch_size, past_key_values.self_attention_cache, seq_length, config
            )
            # For cross attention cache, the seq_length depends on the model, so we remove that dim
            self._check_past_key_values_for_generate(batch_size, past_key_values.cross_attention_cache, None, config)
            return

        # Use the correct config
        config = config.get_text_config(decoder=True)

        # (batch, kv heads, seq_length, head_dim)
        # Only pure mamba models do not have num_attention_heads defined in config, so it can never be 1 in practice for attention models
        num_attention_heads = getattr(config, "num_attention_heads", 1)
        num_kv_heads = getattr(config, "num_key_value_heads", num_attention_heads)
        hidden_size = getattr(config, "d_model", config.hidden_size)
        head_dim = getattr(config, "head_dim", hidden_size // num_attention_heads)

        # For cross attention cache, the seq_length depends on the model, so we remove that dim
        attention_shape = (
            (batch_size, num_kv_heads, seq_length, head_dim)
            if seq_length is not None
            else (batch_size, num_kv_heads, head_dim)
        )

        # For mamba layers
        conv_shape = self._get_conv_state_shape(batch_size, config)
        recurrent_shape = self._get_recurrent_state_shape(batch_size, config)

        # Check the size is coherent
        num_hidden_layers = config.num_hidden_layers
        if getattr(config, "num_kv_shared_layers", None) is not None:
            num_hidden_layers -= config.num_kv_shared_layers
        self.assertEqual(num_hidden_layers, len(past_key_values))

        # Check each layer has the correct shape
        for layer in past_key_values.layers:
            # Mamba + Attention layer cache
            if type(layer) is LinearAttentionAndFullAttentionLayer:
                # Remove the seq_length dim for cross-attention cache (it changes based on the model)
                keys = layer.keys if seq_length is not None else layer.keys[:, :, 0, :]
                values = layer.values if seq_length is not None else layer.values[:, :, 0, :]
                self.assertEqual(keys.shape, attention_shape)
                self.assertEqual(values.shape, attention_shape)
                self.assertEqual(layer.conv_states.shape, conv_shape)
                # May not be used (e.g. lfm2)
                if layer.is_recurrent_states_initialized:
                    self.assertEqual(layer.recurrent_states.shape, recurrent_shape)
            # Mamba only layer cache
            elif type(layer) is LinearAttentionLayer:
                self.assertEqual(layer.conv_states.shape, conv_shape)
                # May not be used (e.g. lfm2)
                if layer.is_recurrent_states_initialized:
                    self.assertEqual(layer.recurrent_states.shape, recurrent_shape)
            # Attention only layer type
            else:
                # Remove the seq_length dim for cross-attention cache (it changes based on the model)
                keys = layer.keys if seq_length is not None else layer.keys[:, :, 0, :]
                values = layer.values if seq_length is not None else layer.values[:, :, 0, :]
                self.assertEqual(keys.shape, attention_shape)
                self.assertEqual(values.shape, attention_shape)