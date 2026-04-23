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

        # Apply ST projector
        if self.projector is not None:
            embeddings = self.projector(pooled_data)
        else:
            embeddings = pooled_data
        # embeddings shape: [batchsize, embedding_size]

        # for matryoshka representation
        dimensions_list = [pooling_param.dimensions for pooling_param in pooling_params]
        if any(d is not None for d in dimensions_list):
            # change the output dimension
            assert len(embeddings) == len(dimensions_list)
            if len(set(dimensions_list)) == 1 and not isinstance(embeddings, list):
                # if all dimensions are the same
                d = dimensions_list[0]
                embeddings = embeddings[..., :d]
            else:
                embeddings = [
                    vecs if d is None else vecs[..., :d]
                    for vecs, d in zip(embeddings, dimensions_list)
                ]

        # for normalize
        if self.activation is not None:
            flags = [p.use_activation for p in pooling_params]
            if len(set(flags)) == 1:
                if flags[0]:
                    embeddings = self.activation(embeddings)
            else:
                embeddings = [
                    self.activation(vecs) if f else vecs
                    for vecs, f in zip(embeddings, flags)
                ]

        # embeddings shape: [batchsize, embedding_size]
        return embeddings