def _get_configured_masks(self) -> list[str]:
        """Obtain a list of configured training masks

        Returns
        -------
        list of configured masks types in the order [<face mask type>, <eye>, <mouth>]
        """
        retval = []
        if cfg.Loss.mask_type() is not None and (cfg.Loss.learn_mask() or
                                                 cfg.Loss.penalized_mask_loss()):
            retval.append(cfg.Loss.mask_type())
        if cfg.Loss.penalized_mask_loss() and cfg.Loss.eye_multiplier() > 1:
            retval.append("eye")
        if cfg.Loss.penalized_mask_loss() and cfg.Loss.mouth_multiplier() > 1:
            retval.append("mouth")
        logger.debug("[%s] Configured masks: %s", self._name, retval)
        return retval