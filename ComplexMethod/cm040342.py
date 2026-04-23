def predict(
        self, x, batch_size=None, verbose="auto", steps=None, callbacks=None
    ):
        # Create an iterator that yields batches of input data.
        epoch_iterator = JAXEpochIterator(
            x=x,
            batch_size=batch_size,
            steps_per_epoch=steps,
            shuffle=False,
            steps_per_execution=self.steps_per_execution,
        )

        if not all(layer.built for layer in self._flatten_layers()):
            # Build the model on one batch of data.
            for _, _, iterator in epoch_iterator:
                # Build model
                x, _, _ = data_adapter_utils.unpack_x_y_sample_weight(
                    next(iterator)
                )
                if is_nnx_enabled():
                    self(x)
                else:
                    with backend.StatelessScope():
                        self(x)
                break
            epoch_iterator.reset()
        # Container that configures and calls callbacks.
        if not isinstance(callbacks, callbacks_module.CallbackList):
            callbacks = callbacks_module.CallbackList(
                callbacks,
                add_progbar=verbose != 0,
                verbose=verbose,
                epochs=1,
                steps=epoch_iterator.num_batches,
                model=self,
            )

        self.make_predict_function()
        self.stop_predicting = False
        callbacks.on_predict_begin()

        def append_to_outputs(batch_outputs, outputs):
            if outputs is None:
                outputs = tree.map_structure(
                    lambda batch_output: [batch_output],
                    batch_outputs,
                )
            else:
                tree.map_structure_up_to(
                    batch_outputs,
                    lambda output, batch_output: output.append(batch_output),
                    outputs,
                    batch_outputs,
                )
            return outputs

        self._jax_state_synced = True
        outputs = None
        non_trainable_variables = None
        with epoch_iterator.catch_stop_iteration():
            for begin_step, end_step, iterator in epoch_iterator:
                callbacks.on_predict_batch_begin(begin_step)
                if self._jax_state_synced:
                    # The state may have been synced by a callback.
                    state = self._get_jax_state(
                        trainable_variables=True,
                        non_trainable_variables=True,
                        purge_model_variables=True,
                    )
                    self._jax_state_synced = False
                batch_outputs, state = self.predict_function(state, iterator)
                (
                    trainable_variables,
                    non_trainable_variables,
                ) = state
                self._jax_state = {
                    "trainable_variables": trainable_variables,
                    # I wouldn't recommend modifying non-trainable model state
                    # during predict(), but it's allowed.
                    "non_trainable_variables": non_trainable_variables,
                }
                outputs = append_to_outputs(batch_outputs, outputs)

                # Dispatch callbacks. This takes care of async dispatch.
                callbacks.on_predict_batch_end(
                    end_step, {"outputs": batch_outputs}
                )

                if self.stop_predicting:
                    break

        self.jax_state_sync()
        callbacks.on_predict_end()
        self._jax_state = None
        return tree.map_structure_up_to(batch_outputs, np.concatenate, outputs)