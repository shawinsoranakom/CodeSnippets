def _init_weights(self, module):
        """Initialize the weights"""
        factor = self.config.initializer_factor  # Used for testing weights initialization
        if isinstance(module, UMT5LayerNorm):
            init.constant_(module.weight, factor * 1.0)
        elif isinstance(
            module,
            (
                UMT5Model,
                UMT5ForConditionalGeneration,
                UMT5EncoderModel,
                UMT5ForQuestionAnswering,
            ),
        ):
            # Mesh TensorFlow embeddings initialization
            # See https://github.com/tensorflow/mesh/blob/fa19d69eafc9a482aff0b59ddd96b025c0cb207d/mesh_tensorflow/layers.py#L1624
            init.normal_(module.shared.weight, mean=0.0, std=factor * 1.0)
            if hasattr(module, "lm_head") and not self.config.tie_word_embeddings:
                init.normal_(module.lm_head.weight, mean=0.0, std=factor * 1.0)
            if hasattr(module, "qa_outputs"):
                init.normal_(module.qa_outputs.weight, mean=0.0, std=factor * ((self.config.d_model) ** -0.5))
                init.zeros_(module.qa_outputs.bias)
        elif isinstance(module, UMT5ForTokenClassification):
            if hasattr(module, "classifier"):
                init.normal_(module.classifier.weight, mean=0.0, std=factor * 1.0)
                init.zeros_(module.classifier.bias)
        elif isinstance(module, UMT5ClassificationHead):
            init.normal_(module.dense.weight, mean=0.0, std=factor * ((self.config.d_model) ** -0.5))
            if hasattr(module.dense, "bias") and module.dense.bias is not None:
                init.zeros_(module.dense.bias)
            init.normal_(module.out_proj.weight, mean=0.0, std=factor * ((self.config.d_model) ** -0.5))
            if hasattr(module.out_proj, "bias") and module.out_proj.bias is not None:
                init.zeros_(module.out_proj.bias)
        elif isinstance(module, UMT5DenseActDense):
            # Mesh TensorFlow FF initialization
            # See https://github.com/tensorflow/mesh/blob/master/mesh_tensorflow/transformer/transformer_layers.py#L56
            # and https://github.com/tensorflow/mesh/blob/fa19d69eafc9a482aff0b59ddd96b025c0cb207d/mesh_tensorflow/layers.py#L89
            init.normal_(module.wi.weight, mean=0.0, std=factor * ((self.config.d_model) ** -0.5))
            if hasattr(module.wi, "bias") and module.wi.bias is not None:
                init.zeros_(module.wi.bias)
            init.normal_(module.wo.weight, mean=0.0, std=factor * ((self.config.d_ff) ** -0.5))
            if hasattr(module.wo, "bias") and module.wo.bias is not None:
                init.zeros_(module.wo.bias)
        elif isinstance(module, UMT5DenseGatedActDense):
            init.normal_(module.wi_0.weight, mean=0.0, std=factor * ((self.config.d_model) ** -0.5))
            if hasattr(module.wi_0, "bias") and module.wi_0.bias is not None:
                init.zeros_(module.wi_0.bias)
            init.normal_(module.wi_1.weight, mean=0.0, std=factor * ((self.config.d_model) ** -0.5))
            if hasattr(module.wi_1, "bias") and module.wi_1.bias is not None:
                init.zeros_(module.wi_1.bias)
            init.normal_(module.wo.weight, mean=0.0, std=factor * ((self.config.d_ff) ** -0.5))
            if hasattr(module.wo, "bias") and module.wo.bias is not None:
                init.zeros_(module.wo.bias)
        elif isinstance(module, UMT5Attention):
            # Mesh TensorFlow attention initialization to avoid scaling before softmax
            # See https://github.com/tensorflow/mesh/blob/fa19d69eafc9a482aff0b59ddd96b025c0cb207d/mesh_tensorflow/transformer/attention.py#L136
            d_model = self.config.d_model
            key_value_proj_dim = self.config.d_kv
            n_heads = self.config.num_heads
            init.normal_(module.q.weight, mean=0.0, std=factor * ((d_model * key_value_proj_dim) ** -0.5))
            init.normal_(module.k.weight, mean=0.0, std=factor * (d_model**-0.5))
            init.normal_(module.v.weight, mean=0.0, std=factor * (d_model**-0.5))
            init.normal_(module.o.weight, mean=0.0, std=factor * ((n_heads * key_value_proj_dim) ** -0.5))
            if module.has_relative_attention_bias:
                init.normal_(module.relative_attention_bias.weight, mean=0.0, std=factor * ((d_model) ** -0.5))