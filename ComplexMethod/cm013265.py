def train_batch(
        self,
        mini_batch: FeatureSet,
        trainer_has_less_inputs: bool,
        simulate_uneven_inputs: bool,
    ):
        grads_dict = None

        if not simulate_uneven_inputs:
            input_batches = [mini_batch]
        else:
            # Split into microbatches, and trim to simulate uneven inputs.
            dense_features = mini_batch.dense_features
            sparse_features = mini_batch.sparse_features
            values = mini_batch.values

            dense_microbatch = torch.split(dense_features, 2)
            sparse_microbatch = torch.split(sparse_features, 2)
            values_microbatch = torch.split(values, 2)
            batches = []
            for d, s, v in zip(
                dense_microbatch, sparse_microbatch, values_microbatch, strict=True
            ):
                feature_set = FeatureSet(dense_features=d, sparse_features=s, values=v)
                batches.append(feature_set)

            if trainer_has_less_inputs:
                input_batches = batches[: len(batches) // 2]
                gLogger.info(
                    "Trainer reduced input patches from %s "
                    "to %s to simulate uneven inputs.",
                    len(batches),
                    len(input_batches),
                )
            else:
                input_batches = batches

        with (
            self.hybrid_module.join()
            if simulate_uneven_inputs
            else contextlib.nullcontext()
        ):
            for b in input_batches:
                with dist_autograd.context() as context_id:
                    output = self.hybrid_module.forward(b)
                    loss = (output * mini_batch.values).sum()
                    dist_autograd.backward(context_id, [loss])
                    grads_dict = dist_autograd.get_gradients(context_id)
                    gLogger.info(
                        "Loss is %s for mini batch: %s. Grads dict has %s entries: %s",
                        loss,
                        mini_batch,
                        len(grads_dict),
                        grads_dict,
                    )
        return (
            tuple(grads_dict[param] for param in self.ddp_params),
            tuple(grads_dict[param] for param in self.non_ddp_params),
        )