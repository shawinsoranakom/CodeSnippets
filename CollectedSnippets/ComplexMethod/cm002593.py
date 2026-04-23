def tie_weights(self, missing_keys: set[str] | None = None, recompute_mapping: bool = True):
        """
        Tie the model weights. If `recompute_mapping=False` (default when called internally), it will rely on the
        `model.all_tied_weights_keys` attribute, containing the `{target: source}` mapping for the tied params.
        If `recompute_mapping=True`, it will re-check all internal submodels and their config to determine the params
        that need to be tied. This is the default when `model.tie_weights()` is called on its own, outside of
        `__init__`, and `from_pretrained`, in case the config values were changed somewhere.

        Note that during `from_pretrained`, tying is *symmetric*: if the mapping says "tie target -> source" but
        `source` is missing in the checkpoint while `target` exists, we *swap* source and target so we can still
        tie everything to the parameter that actually exists.
        """
        # In this case, the keys stored in `all_tied_weights_keys` are already correct
        if not recompute_mapping:
            tied_keys = self.all_tied_weights_keys
        else:
            tied_keys = self.get_expanded_tied_weights_keys(all_submodels=True)

        tied_keys = list(tied_keys.items())
        for i, (target_param_name, source_param_name) in enumerate(tied_keys):
            # This is `from_pretrained` -> let's check symmetrically in case the source key is not present
            if missing_keys is not None:
                remove_from_missing = True
                source_is_there = source_param_name not in missing_keys
                target_is_there = target_param_name not in missing_keys
                # Both are already present -> it means the config is wrong and do not reflect the actual
                # checkpoint -> let's raise a warning and NOT tie them
                if source_is_there and target_is_there:
                    # If both are present, check if the weights are exactly similar, and only tie in this case
                    # This check is important, as torch `.bin` checkpoints always contain both keys, referencing the same storage
                    if not torch.equal(self.get_parameter(source_param_name), self.get_parameter(target_param_name)):
                        logger.warning(
                            f"The tied weights mapping and config for this model specifies to tie {source_param_name} to "
                            f"{target_param_name}, but both are present in the checkpoints with different values, so we will NOT "
                            "tie them. You should update the config with `tie_word_embeddings=False` to silence this warning."
                        )
                        # Remove from internal attribute to correctly reflect actual tied weights
                        self.all_tied_weights_keys.pop(target_param_name)
                        # Skip to next iteration
                        continue
                # We're missing the source but we have the target -> we swap them, tying the parameter that exists
                elif not source_is_there and target_is_there:
                    target_param_name, source_param_name = source_param_name, target_param_name
                # Both are missing -> check other keys in case more than 2 keys are tied to the same weight
                elif not source_is_there and not target_is_there:
                    for target_backup, source_backup in tied_keys[i + 1 :]:
                        # In case of more than 2 keys tied to the same weight, they are guaranteed to all have
                        # the same source thanks to `get_expanded_tied_weights_keys` so this check is enough
                        if source_backup == source_param_name:
                            target_backup_is_there = target_backup not in missing_keys
                            # If the target is present, we found the correct weight to tie into (we know the source is missing)
                            # Note here that we do not tie the missing source right now as well, as it will be done anyway when
                            # the pair (target_backup, source_backup) becomes the main pair (target_param_name, source_param_name)
                            if target_backup_is_there:
                                source_param_name = target_backup
                                break
                    # If we did not break from the loop, it was impossible to find a source key -> let's raise
                    else:
                        # TODO Cyril: here ideally we want to raise instead of warning, but will break our CI as we have
                        # tests loading model from empty dicts to perform init checks - since we don't raise, add a flag
                        # to NOT remove from missing keys as it's actually still missing
                        remove_from_missing = False
                        logger.warning(
                            f"This checkpoint seem corrupted. The tied weights mapping for this model specifies to tie "
                            f"{source_param_name} to {target_param_name}, but both are absent from the checkpoint, "
                            "and we could not find another related tied weight for those keys"
                        )

            # Perform the actual tying
            source_param = self.get_parameter_or_buffer(source_param_name)
            if "." in target_param_name:
                parent_name, name = target_param_name.rsplit(".", 1)
                parent = self.get_submodule(parent_name)
            else:
                name = target_param_name
                parent = self
            # Tie the weights
            setattr(parent, name, source_param)
            self._adjust_bias(parent, source_param)
            # Remove from missing if necessary
            if missing_keys is not None and remove_from_missing:
                missing_keys.discard(target_param_name)