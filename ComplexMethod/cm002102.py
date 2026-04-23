def _check_caches_are_equal(self, cache1: Cache, cache2: Cache):
        if not isinstance(cache1, Cache) or not isinstance(cache2, Cache):
            raise ValueError("The cache is not standard! Please overwrite `_check_caches_are_equal`")

        # In this case, we simply call recursively the function on both internal caches
        if isinstance(cache1, EncoderDecoderCache):
            self._check_caches_are_equal(cache1.self_attention_cache, cache2.self_attention_cache)
            self._check_caches_are_equal(cache1.cross_attention_cache, cache2.cross_attention_cache)
            return

        if not len(cache1) == len(cache2):
            raise ValueError("Both caches do not have the same number of layers.")

        num_layers = len(cache1)
        for idx in range(num_layers):
            self.assertEqual(type(cache1.layers[idx]), type(cache2.layers[idx]))

            # Mamba + Attention layer
            if type(cache1.layers[idx]) is LinearAttentionAndFullAttentionLayer:
                torch.testing.assert_close(cache1.layers[idx].keys, cache2.layers[idx].keys)
                torch.testing.assert_close(cache1.layers[idx].values, cache2.layers[idx].values)
                torch.testing.assert_close(cache1.layers[idx].conv_states, cache2.layers[idx].conv_states)
                # May not be used (e.g. lfm2)
                if cache1.layers[idx].is_recurrent_states_initialized:
                    torch.testing.assert_close(
                        cache1.layers[idx].recurrent_states, cache2.layers[idx].recurrent_states
                    )
            # Mamba layer
            elif type(cache1.layers[idx]) is LinearAttentionLayer:
                torch.testing.assert_close(cache1.layers[idx].conv_states, cache2.layers[idx].conv_states)
                # May not be used (e.g. lfm2)
                if cache1.layers[idx].is_recurrent_states_initialized:
                    torch.testing.assert_close(
                        cache1.layers[idx].recurrent_states, cache2.layers[idx].recurrent_states
                    )
            # Attention layer
            else:
                torch.testing.assert_close(cache1.layers[idx].keys, cache2.layers[idx].keys)
                torch.testing.assert_close(cache1.layers[idx].values, cache2.layers[idx].values)