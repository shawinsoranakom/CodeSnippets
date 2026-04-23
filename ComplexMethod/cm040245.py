def call(self, inputs, training=None, mask=None, **kwargs):
        if self._functional:
            return self._functional.call(
                inputs, training=training, mask=mask, **kwargs
            )

        # Fallback: Just apply the layer sequence.
        # This typically happens if `inputs` is a nested struct.
        for layer in self.layers:
            # During each iteration, `inputs` are the inputs to `layer`, and
            # `outputs` are the outputs of `layer` applied to `inputs`. At the
            # end of each iteration `inputs` is set to `outputs` to prepare for
            # the next layer.
            layer_kwargs = {
                k: kwargs[k]
                # only inject if this layer’s signature actually has that arg
                for k in getattr(layer, "_call_has_context_arg", {})
                if k in kwargs
            }
            if layer._call_has_mask_arg:
                layer_kwargs["mask"] = mask
            if layer._call_has_training_arg and training is not None:
                layer_kwargs["training"] = training
            outputs = layer(inputs, **layer_kwargs)
            inputs = outputs

            mask = tree.map_structure(backend.get_keras_mask, outputs)
        return outputs