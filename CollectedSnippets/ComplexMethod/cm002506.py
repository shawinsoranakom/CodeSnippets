def _load_callback_state(self) -> None:
        """If callback states exist and were passed in, restore their states if enabled"""
        if not self.args.restore_callback_states_from_checkpoint:
            return
        # Callback states are stored in stateful_callbacks
        not_found = []
        new_callbacks = []
        original_callbacks = self.callback_handler.callbacks + [self.control]
        for stored_callback, data in self.state.stateful_callbacks.items():
            if not isinstance(data, list):
                data = [data]
            if any(callback.__class__.__name__ == stored_callback for callback in original_callbacks):
                # We can load/restore from multiple callbacks of the same type.
                duplicates = [
                    callback for callback in original_callbacks if callback.__class__.__name__ == stored_callback
                ]
                for callback, callback_data in zip(duplicates, data):
                    args = callback_data.get("args", {})
                    attributes = callback_data.get("attributes", {})
                    new_callback = type(callback)(**args)
                    for attribute, value in attributes.items():
                        setattr(new_callback, attribute, value)
                    if isinstance(callback, TrainerControl):
                        # Specifically for restoring the `control` state
                        self.control = new_callback
                    else:
                        new_callbacks.append(new_callback)
                    # We remove the existing callback and add it to the list of new callbacks
                    self.callback_handler.remove_callback(type(new_callback))
                logger.info("Continuing training from checkpoint, restoring any callbacks that were passed in")
            else:
                not_found.append(stored_callback)
        if len(not_found) > 0:
            logger.warning(
                f"Checkpoint included callbacks not included in current configuration. Ignoring. ({', '.join(not_found)})"
            )
        for callback in new_callbacks:
            self.callback_handler.add_callback(callback)