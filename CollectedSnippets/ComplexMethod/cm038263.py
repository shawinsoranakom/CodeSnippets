def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        total_num_heads = self.config.num_attention_heads
        if self.config.new_decoder_architecture:
            total_num_kv_heads = self.config.num_kv_heads
        elif self.config.multi_query:
            total_num_kv_heads = 1
        else:
            total_num_kv_heads = total_num_heads
        num_query_heads_per_kv_head = total_num_heads // total_num_kv_heads
        params_dict = dict(self.named_parameters(remove_duplicate=False))
        loaded_params: set[str] = set()
        for name, loaded_weight in weights:
            # Skip loading extra bias for GPTQ models.
            if name.endswith(".bias") and name not in params_dict:
                continue
            if is_pp_missing_parameter(name, self):
                continue
            param = params_dict[name]
            if "query_key_value" in name:
                output_dim = getattr(param, "output_dim", None)
                loaded_weight_shape = loaded_weight.shape
                if output_dim is not None:
                    loaded_weight = loaded_weight.view(
                        loaded_weight_shape[:output_dim]
                        + (total_num_kv_heads, num_query_heads_per_kv_head + 2, -1)
                        + loaded_weight_shape[output_dim + 1 :]
                    )
                    wq = loaded_weight.narrow(
                        output_dim + 1, 0, num_query_heads_per_kv_head
                    ).reshape(
                        *loaded_weight_shape[:output_dim],
                        -1,
                        *loaded_weight_shape[output_dim + 1 :],
                    )
                    wk = loaded_weight.narrow(
                        output_dim + 1, num_query_heads_per_kv_head, 1
                    ).reshape(
                        *loaded_weight_shape[:output_dim],
                        -1,
                        *loaded_weight_shape[output_dim + 1 :],
                    )
                    wv = loaded_weight.narrow(
                        output_dim + 1, num_query_heads_per_kv_head + 1, 1
                    ).reshape(
                        *loaded_weight_shape[:output_dim],
                        -1,
                        *loaded_weight_shape[output_dim + 1 :],
                    )
                    loaded_weight = torch.cat([wq, wk, wv], dim=output_dim)

            weight_loader = getattr(param, "weight_loader", default_weight_loader)
            weight_loader(param, loaded_weight)
            loaded_params.add(name)
        return loaded_params