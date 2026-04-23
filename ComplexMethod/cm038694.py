def custom_op_log_check(self):
        """
        This method logs the enabled/disabled custom ops and checks that the
        passed custom_ops field only contains relevant ops.
        It is called at the end of set_current_vllm_config,
        after the custom ops have been instantiated.
        """

        if len(self.enabled_custom_ops) + len(self.disabled_custom_ops) == 0:
            logger.debug("No custom ops found in model.")
            return

        logger.debug("enabled custom ops: %s", self.enabled_custom_ops)
        logger.debug("disabled custom ops: %s", self.disabled_custom_ops)

        all_ops_in_model = self.enabled_custom_ops | self.disabled_custom_ops
        for op in self.custom_ops:
            if op in {"all", "none"}:
                continue

            assert op[0] in {"+", "-"}, (
                "Invalid custom op syntax (should be checked during init)"
            )

            # check if op name exists in model
            op_name = op[1:]
            if op_name not in all_ops_in_model:
                from vllm.model_executor.custom_op import op_registry

                # Does op exist at all or is it just not present in this model?
                # Note: Only imported op classes appear in the registry.
                missing_str = (
                    "doesn't exist (or wasn't imported/registered)"
                    if op_name not in op_registry
                    else "not present in model"
                )

                enable_str = "enabling" if op[0] == "+" else "disabling"
                logger.warning_once(
                    "Op '%s' %s, %s with '%s' has no effect",
                    op_name,
                    missing_str,
                    enable_str,
                    op,
                )