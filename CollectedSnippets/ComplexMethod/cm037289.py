def _maybe_share_lm_head(self, target_language_model: nn.Module) -> None:
        """
        Some draft models may not have their own LM head, and some may have a
        duplicate copy of the target model's LM head. In these cases, we share
        the target model's LM head with the draft model to save memory.
        """
        share_lm_head = False
        if hasattr(self.model, "has_own_lm_head"):
            # EAGLE model
            if not self.model.has_own_lm_head:
                share_lm_head = True
                logger.info(
                    "Detected EAGLE model without its own lm_head in the checkpoint. "
                    "Sharing target model lm_head weights with the draft model."
                )
            elif (
                hasattr(target_language_model, "lm_head")
                and hasattr(target_language_model.lm_head, "weight")
                and hasattr(self.model.lm_head, "weight")
                and isinstance(target_language_model.lm_head.weight, torch.Tensor)
                and isinstance(self.model.lm_head.weight, torch.Tensor)
                # TODO: Offload to CPU for comparison to avoid extra GPU memory
                # usage in CI testing environments with limited GPU memory
                and torch.equal(
                    target_language_model.lm_head.weight.cpu(),
                    self.model.lm_head.weight.cpu(),
                )
            ):
                share_lm_head = True
                logger.info(
                    "Detected EAGLE model with lm_head identical to the target model. "
                    "Sharing target model lm_head weights with the draft model."
                )
            else:
                logger.info(
                    "Detected EAGLE model with distinct lm_head weights. "
                    "Keeping separate lm_head weights from the target model."
                )
        else:
            # MTP model
            share_lm_head = True
            logger.info(
                "Detected MTP model. "
                "Sharing target model lm_head weights with the draft model."
            )

        if share_lm_head and hasattr(target_language_model, "lm_head"):
            if hasattr(self.model, "lm_head"):
                del self.model.lm_head
            self.model.lm_head = target_language_model.lm_head

            # MTP models call compute_logits via shared_head.head (a
            # ParallelLMHead inside each MTP layer), not self.model.lm_head.
            # If the checkpoint omits a copy of the lm_head weights at the
            # MTP layer path, shared_head.head stays uninitialised and
            # produces NaN logits. Always share it explicitly.
            inner = getattr(self.model, "model", None)
            layers = getattr(inner, "layers", None) if inner else None
            if layers is not None:
                items = layers.values() if isinstance(layers, nn.ModuleDict) else layers
                for layer in items:
                    sh = getattr(layer, "shared_head", None)
                    if sh is not None and hasattr(sh, "head"):
                        del sh.head
                        sh.head = target_language_model.lm_head
                        logger.info(
                            "Shared target model lm_head with MTP shared_head.head."
                        )

        if self.use_local_argmax_reduction:
            if not hasattr(self.model, "get_top_tokens"):
                raise ValueError(
                    "use_local_argmax_reduction is enabled but draft model "
                    f"{self.model.__class__.__name__} does not implement "
                    "get_top_tokens()."
                )
            # Warn if draft model has vocab remapping, which forces fallback
            # to the full-logits path (negating the optimization).
            if (
                hasattr(self.model, "draft_id_to_target_id")
                and self.model.draft_id_to_target_id is not None
            ):
                logger.warning(
                    "use_local_argmax_reduction is enabled but draft model "
                    "uses draft_id_to_target_id vocab remapping. The "
                    "optimization will be bypassed (falling back to full "
                    "logits gather + argmax)."
                )
            else:
                logger.info(
                    "Using local argmax reduction for draft token generation "
                    "(communication: O(2*tp_size) vs O(vocab_size))."
                )