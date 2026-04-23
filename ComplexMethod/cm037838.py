def forward_chunk(
        self,
        pooled_data: TokenPoolingMethodOutputItem,
        pooling_param: PoolingParams,
    ) -> TokenPoolerHeadOutputItem:
        # for unfinished chunked prefill
        if pooled_data is None:
            return None

        if self.head_dtype is not None:
            pooled_data = pooled_data.to(self.head_dtype)
        # hidden_states shape: [n_token, hidden_size]

        if self.classifier is not None:
            logits = self.classifier(pooled_data)
        else:
            logits = pooled_data
        # logits shape: [n_token, num_labels]

        # Affine score calibration: activation((logit - mean) / sigma)
        if self.logit_mean is not None:
            logits = logits - self.logit_mean
        if self.logit_sigma is not None:
            logits = logits / self.logit_sigma

        if self.activation is not None and pooling_param.use_activation:
            logits = self.activation(logits)

        # logits shape: [n_token, num_labels]
        return logits