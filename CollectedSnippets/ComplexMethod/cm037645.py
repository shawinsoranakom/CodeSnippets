def _get_weight_size(
        self,
        layer: torch.nn.Module,
        scheme: TransformScheme,
        args: TransformArgs,
        input_size: int,
        output_size: int,
    ) -> int:
        if scheme.head_dim is not None:
            return scheme.head_dim

        if isinstance(layer, LinearBase):
            if args.location == TransformLocation.INPUT:
                return input_size

            elif args.location == TransformLocation.OUTPUT:
                return output_size

        elif isinstance(layer, VocabParallelEmbedding):
            if args.location == TransformLocation.INPUT:
                return output_size

            elif args.location == TransformLocation.OUTPUT:
                return input_size

        raise ValueError()