def forward(
        self,
        positions: torch.Tensor,
        hidden_states: torch.Tensor,
    ) -> torch.Tensor:
        residual = hidden_states

        if self.config.num_ln_in_parallel_attn == 2:
            attention_layernorm_out = self.ln_attn(hidden_states)
            mlp_layernorm_out = self.ln_mlp(hidden_states)
        else:
            attention_layernorm_out = self.input_layernorm(hidden_states)

        # Self attention.
        attention_output, attention_bias = self.self_attention(
            positions=positions,
            hidden_states=attention_layernorm_out,
        )
        if self.reduce_row_parallel_results and attention_bias is not None:
            attention_output += attention_bias

        if not self.config.new_decoder_architecture:
            if self.config.parallel_attn:
                mlp_layernorm_out = attention_layernorm_out
            else:
                residual += attention_output
                mlp_layernorm_out = self.post_attention_layernorm(residual)

        if (
            self.config.new_decoder_architecture
            and self.config.parallel_attn
            and self.config.num_ln_in_parallel_attn == 1
        ):
            mlp_layernorm_out = attention_layernorm_out

        # MLP.
        mlp_output, mlp_bias = self.mlp(mlp_layernorm_out)
        if self.reduce_row_parallel_results and mlp_bias is not None:
            mlp_output += mlp_bias

        if not self.reduce_row_parallel_results:
            # When MLP and Attention layers are parallel, we can use
            # only one all-reduce operator to reduce the results from
            # both MLP and Attention layers.
            mlp_output += attention_output
            mlp_output = tensor_model_parallel_all_reduce(mlp_output)
            if attention_bias is not None:
                mlp_output += attention_bias
            if mlp_bias is not None:
                mlp_output += mlp_bias

        output = mlp_output + residual
        return output