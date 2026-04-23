def _update_legacy_config(self) -> bool:
        """ Legacy updates for new config additions.

        When new config items are added to the Faceswap code, existing model state files need to be
        updated to handle these new items.

        Current existing legacy update items:

            * loss - If old `dssim_loss` is ``true`` set new `loss_function` to `ssim` otherwise
            set it to `mae`. Remove old `dssim_loss` item

            * l2_reg_term - If this exists, set loss_function_2 to ``mse`` and loss_weight_2 to
            the value held in the old ``l2_reg_term`` item

            * masks - If `learn_mask` does not exist then it is set to ``True`` if `mask_type` is
            not ``None`` otherwise it is set to ``False``.

            * masks type - Replace removed masks 'dfl_full' and 'facehull' with `components` mask

            * clipnorm - Only existed in 2 models (DFL-SAE + Unbalanced). Replaced with global
            option autoclip

            * Clip model - layer names have had to be changed to replace dots with underscores, so
            replace these

        Returns
        -------
        bool
            ``True`` if legacy items exist and state file has been updated, otherwise ``False``
        """
        logger.debug("Checking for legacy state file update")
        priors = ["dssim_loss", "mask_type", "mask_type", "l2_reg_term", "clipnorm", "autoclip"]
        new_items = ["loss_function", "learn_mask", "mask_type", "loss_function_2",
                     "gradient_clipping", "clipping"]
        updated = False
        for old, new in zip(priors, new_items):
            if old not in self._config:
                logger.debug("Legacy item '%s' not in state config. Skipping update", old)
                continue

            # dssim_loss > loss_function
            if old == "dssim_loss":
                self._config[new] = "ssim" if self._config[old] else "mae"
                del self._config[old]
                updated = True
                logger.info("Updated state config from legacy dssim format. New config loss "
                            "function: '%s'", self._config[new])
                continue

            # Add learn mask option and set to True if model has "penalized_mask_loss" specified
            if old == "mask_type" and new == "learn_mask" and new not in self._config:
                self._config[new] = self._config["mask_type"] is not None
                updated = True
                logger.info("Added new 'learn_mask' state config item for this model. Value set "
                            "to: %s", self._config[new])
                continue

            # Replace removed masks with most similar equivalent
            if old == "mask_type" and new == "mask_type" and self._config[old] in ("facehull",
                                                                                   "dfl_full"):
                old_mask = self._config[old]
                self._config[new] = "components"
                updated = True
                logger.info("Updated 'mask_type' from '%s' to '%s' for this model",
                            old_mask, self._config[new])

            # Replace l2_reg_term with the correct loss_2_function and update the value of
            # loss_2_weight
            if old == "l2_reg_term":
                self._config[new] = "mse"
                self._config["loss_weight_2"] = self._config[old]
                del self._config[old]
                updated = True
                logger.info("Updated state config from legacy 'l2_reg_term' to 'loss_function_2'")

            # Replace clipnorm with correct gradient clipping type and value
            if old == "clipnorm":
                self._config[new] = "norm"
                del self._config[old]
                updated = True
                logger.info("Updated state config from legacy '%s' to  '%s: %s'", old, new, old)

            # Replace autoclip with correct gradient clipping type
            if old == "autoclip":
                self._config[new] = old
                del self._config[old]
                updated = True
                logger.info("Updated state config from legacy '%s' to '%s: %s'", old, new, old)

        # Update Clip layer names from dots to underscores
        mixed_precision = self._mixed_precision_layers
        if any("." in name for name in mixed_precision):
            self._mixed_precision_layers = [x.replace(".", "_") for x in mixed_precision]
            updated = True
            logger.info("Updated state config for legacy 'mixed_precision' storage of Clip layers")

        logger.debug("State file updated for legacy config: %s", updated)
        return updated