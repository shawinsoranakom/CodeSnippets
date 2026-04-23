def fit(
        self,
        x=None,
        y=None,
        batch_size=None,
        epochs=1,
        verbose="auto",
        callbacks=None,
        validation_split=0.0,
        validation_data=None,
        shuffle=True,
        class_weight=None,
        sample_weight=None,
        initial_epoch=0,
        steps_per_epoch=None,
        validation_steps=None,
        validation_batch_size=None,
        validation_freq=1,
    ):
        self._assert_compile_called("fit")
        # Possibly cap epochs for debugging runs.
        max_epochs = config.max_epochs()
        if max_epochs and max_epochs < epochs:
            warnings.warn("Limiting epochs to %d" % max_epochs)
            epochs = max_epochs
        # TODO: respect compiled trainable state
        self._eval_epoch_iterator = None
        if validation_split and validation_data is None:
            # Create the validation data using the training data. Only supported
            # for TF/numpy/jax arrays.
            (
                (x, y, sample_weight),
                validation_data,
            ) = array_slicing.train_validation_split(
                (x, y, sample_weight), validation_split=validation_split
            )

        if validation_data is not None:
            (
                val_x,
                val_y,
                val_sample_weight,
            ) = data_adapter_utils.unpack_x_y_sample_weight(validation_data)

        # Create an iterator that yields batches for one epoch.
        epoch_iterator = JAXEpochIterator(
            x=x,
            y=y,
            sample_weight=sample_weight,
            batch_size=batch_size,
            steps_per_epoch=steps_per_epoch,
            shuffle=shuffle,
            class_weight=class_weight,
            steps_per_execution=self.steps_per_execution,
        )

        self._symbolic_build(iterator=epoch_iterator)
        epoch_iterator.reset()

        # Container that configures and calls callbacks.
        if not isinstance(callbacks, callbacks_module.CallbackList):
            callbacks = callbacks_module.CallbackList(
                callbacks,
                add_history=True,
                add_progbar=verbose != 0,
                verbose=verbose,
                epochs=epochs,
                steps=epoch_iterator.num_batches,
                model=self,
            )

        self.make_train_function()
        self.stop_training = False
        training_logs = {}
        training_finished = False
        callbacks.on_train_begin()
        initial_epoch = self._initial_epoch or initial_epoch
        try:
            for epoch in range(initial_epoch, epochs):
                self.reset_metrics()
                callbacks.on_epoch_begin(epoch)

                self._jax_state_synced = True
                with epoch_iterator.catch_stop_iteration():
                    for begin_step, end_step, iterator in epoch_iterator:
                        # Callbacks
                        callbacks.on_train_batch_begin(begin_step)

                        # Train step
                        if self._jax_state_synced:
                            # The state may have been synced by a callback.
                            state = self._get_jax_state(
                                trainable_variables=True,
                                non_trainable_variables=True,
                                optimizer_variables=True,
                                metrics_variables=True,
                                purge_model_variables=True,
                            )
                            self._jax_state_synced = False

                        logs, state = self.train_function(state, iterator)
                        (
                            trainable_variables,
                            non_trainable_variables,
                            optimizer_variables,
                            metrics_variables,
                        ) = state

                        # Setting _jax_state enables callbacks to force a state
                        # sync if they need to.
                        self._jax_state = {
                            "trainable_variables": trainable_variables,
                            "non_trainable_variables": non_trainable_variables,
                            "optimizer_variables": optimizer_variables,
                            "metrics_variables": metrics_variables,
                        }
                        # Dispatch callbacks. This takes care of async dispatch.
                        callbacks.on_train_batch_end(end_step, logs)

                        if self.stop_training:
                            # Stop training if a callback has set
                            # this flag in on_(train_)batch_end.
                            break

                # Reattach state to the model
                # (if not already done by a callback).
                # NOTE: doing this after each step would be a big performance
                # bottleneck.
                self.jax_state_sync()

                # Override with model metrics instead of last step logs if
                # needed.
                epoch_logs = dict(self._get_metrics_result_or_logs(logs))

                # Run validation.
                if validation_data is not None and self._should_eval(
                    epoch, validation_freq
                ):
                    # Create JAXEpochIterator for evaluation and cache it.
                    if getattr(self, "_eval_epoch_iterator", None) is None:
                        self._eval_epoch_iterator = JAXEpochIterator(
                            x=val_x,
                            y=val_y,
                            sample_weight=val_sample_weight,
                            batch_size=validation_batch_size or batch_size,
                            steps_per_execution=self.steps_per_execution,
                            steps_per_epoch=validation_steps,
                            shuffle=False,
                        )
                    val_logs = self.evaluate(
                        x=val_x,
                        y=val_y,
                        sample_weight=val_sample_weight,
                        batch_size=validation_batch_size or batch_size,
                        steps=validation_steps,
                        callbacks=callbacks,
                        return_dict=True,
                        _use_cached_eval_dataset=True,
                    )
                    val_logs = {
                        f"val_{name}": val for name, val in val_logs.items()
                    }
                    epoch_logs.update(val_logs)

                callbacks.on_epoch_end(epoch, epoch_logs)
                training_logs = epoch_logs
                if self.stop_training:
                    break
            training_finished = True

        finally:
            self.jax_state_sync()
            if (
                isinstance(self.optimizer, optimizers_module.Optimizer)
                and epochs > 0
            ):
                self.optimizer.finalize_variable_values(self.trainable_weights)

            # If _eval_epoch_iterator exists, delete it after all epochs
            # are done.
            if getattr(self, "_eval_epoch_iterator", None) is not None:
                del self._eval_epoch_iterator
            if training_finished:
                callbacks.on_train_end(logs=training_logs)
            self._jax_state = None
        return self.history