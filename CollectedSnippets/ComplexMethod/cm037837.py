def forward(
        self,
        pooled_data: SequencePoolingMethodOutput,
        pooling_metadata: PoolingMetadata,
    ) -> SequencePoolerHeadOutput:
        pooling_params = pooling_metadata.pooling_params
        assert len(pooled_data) == len(pooling_params)

        if isinstance(pooled_data, list):
            pooled_data = torch.stack(pooled_data)
        # pooled_data shape: [batchsize, hidden_size]

        if self.head_dtype is not None:
            pooled_data = pooled_data.to(self.head_dtype)

        if self.classifier is not None:
            logits = self.classifier(pooled_data)
        else:
            logits = pooled_data

        # logits shape: [batchsize, num_labels]
        # Affine score calibration: activation((logit - mean) / sigma)
        if self.logit_mean is not None:
            logits = logits - self.logit_mean
        if self.logit_sigma is not None:
            logits = logits / self.logit_sigma

        if self.activation is not None:
            flags = [p.use_activation for p in pooling_params]
            if len(set(flags)) == 1:
                logits = self.activation(logits) if flags[0] else logits
            else:
                logits = [
                    self.activation(vecs) if f else vecs
                    for vecs, f in zip(logits, flags)
                ]

        # logits shape: [batchsize, num_labels]
        return logits