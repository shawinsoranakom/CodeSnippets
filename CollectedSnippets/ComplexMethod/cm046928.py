def PatchRL(FastLanguageModel):
    try:
        from trl.models.utils import unwrap_model_for_generation
    except ImportError:
        try:
            from trl.models import unwrap_model_for_generation
        except ImportError:
            # Local fallback -- TRL removed or moved this symbol
            from contextlib import contextmanager as _cm

            @_cm
            def unwrap_model_for_generation(
                model, accelerator, gather_deepspeed3_params = True
            ):
                unwrapped_model = accelerator.unwrap_model(model)
                is_gc = getattr(unwrapped_model, "is_gradient_checkpointing", False)
                if is_gc:
                    unwrapped_model.gradient_checkpointing_disable()
                if (
                    getattr(accelerator, "state", None) is not None
                    and getattr(accelerator.state, "deepspeed_plugin", None) is not None
                    and accelerator.state.deepspeed_plugin.zero_stage == 3
                ):
                    if not gather_deepspeed3_params:
                        yield accelerator.unwrap_model(model)
                    else:
                        import deepspeed

                        with deepspeed.zero.GatheredParameters(model.parameters()):
                            yield accelerator.unwrap_model(model)
                else:
                    yield unwrapped_model
                if is_gc:
                    unwrapped_model.gradient_checkpointing_enable()

    from contextlib import contextmanager

    @contextmanager
    def unsloth_unwrap_model_for_generation(model, *args, **kwargs):
        with unwrap_model_for_generation(model, *args, **kwargs) as unwrapped_model:
            # Put the model in inference mode.
            FastLanguageModel.for_inference(model)

            # We must use .clone for Unsloth since we force inference_mode
            # Rather we should have used no_grad
            original_generate = unwrapped_model.generate

            def generate_with_clone(*args, **kwargs):
                out = original_generate(*args, **kwargs)
                if isinstance(out, torch.Tensor):
                    return out.clone()
                return out

            unwrapped_model.generate = generate_with_clone

            try:
                yield unwrapped_model
            finally:
                # Restore generate and return
                unwrapped_model.generate = original_generate
                FastLanguageModel.for_training(model)

    from transformers import Trainer
    from transformers.trainer_pt_utils import nested_detach

    @torch.no_grad()
    def unsloth_prediction_step(
        self,
        model,
        inputs,
        prediction_loss_only,
        ignore_keys,
    ):
        """
        Perform an evaluation step on `model` using `inputs`.
        Subclass and override to inject custom behavior.
        Args:
            model (`nn.Module`):
                The model to evaluate.
            inputs (`Dict[str, Union[torch.Tensor, Any]]`):
                The inputs and targets of the model.
                The dictionary will be unpacked before being fed to the model. Most models expect the targets under the
                argument `labels`. Check your model's documentation for all accepted arguments.
            prediction_loss_only (`bool`):
                Whether or not to return the loss only.
            ignore_keys (`List[str]`, *optional*):
                A list of keys in the output of your model (if it is a dictionary) that should be ignored when
                gathering predictions.
        Return:
            Tuple[Optional[torch.Tensor], Optional[torch.Tensor], Optional[torch.Tensor]]: A tuple with the loss,
            logits and labels (each being optional).
        """
        has_labels = (
            False
            if len(self.label_names) == 0
            else all(inputs.get(k) is not None for k in self.label_names)
        )
        # For CLIP-like models capable of returning loss values.
        # If `return_loss` is not specified or being `None` in `inputs`, we check if the default value of `return_loss`
        # is `True` in `model.forward`.
        return_loss = inputs.get("return_loss", None)
        if return_loss is None:
            return_loss = self.can_return_loss
        loss_without_labels = (
            True if len(self.label_names) == 0 and return_loss else False
        )

        inputs = self._prepare_inputs(inputs)
        if ignore_keys is None:
            if hasattr(self.model, "config"):
                ignore_keys = getattr(
                    self.model.config, "keys_to_ignore_at_inference", []
                )
            else:
                ignore_keys = []

        # labels may be popped when computing the loss (label smoothing for instance) so we grab them first.
        if has_labels or loss_without_labels:
            labels = nested_detach(tuple(inputs.get(name) for name in self.label_names))
            if len(labels) == 1:
                labels = labels[0]
        else:
            labels = None

        os.environ["UNSLOTH_RETURN_LOGITS"] = "1"
        with torch.no_grad():
            if has_labels or loss_without_labels:
                with self.compute_loss_context_manager():
                    try:
                        num_items_in_batch = self._get_num_items_in_batch(
                            [inputs], self.args.device
                        )
                    except (AttributeError, TypeError):
                        num_items_in_batch = None
                    loss, outputs = self.compute_loss(
                        model,
                        inputs,
                        return_outputs = True,
                        num_items_in_batch = num_items_in_batch,
                    )
                loss = loss.mean().detach()

                if isinstance(outputs, dict):
                    logits = tuple(
                        v for k, v in outputs.items() if k not in ignore_keys + ["loss"]
                    )
                else:
                    logits = outputs[1:]
            else:
                loss = None
                with self.compute_loss_context_manager():
                    tokenized_output = self.processing_class(
                        inputs["prompt"],
                        padding = True,
                        truncation = True,
                        return_tensors = "pt",
                    ).to(model.device)
                    outputs = model(**tokenized_output)
                if isinstance(outputs, dict):
                    logits = tuple(
                        v for k, v in outputs.items() if k not in ignore_keys
                    )
                else:
                    logits = outputs
                # TODO: this needs to be fixed and made cleaner later.
                if self.args.past_index >= 0:
                    self._past = outputs[self.args.past_index - 1]
        os.environ["UNSLOTH_RETURN_LOGITS"] = "0"
        if prediction_loss_only:
            return (loss, None, None)

        logits = nested_detach(logits)
        if len(logits) == 1:
            logits = logits[0]

        return (loss, logits, labels)

    import trl.trainer

    trainers = dir(trl.trainer)
    trainers = [x for x in trainers if x.endswith("_trainer")]
    unwrap = "unwrap_model_for_generation"
    for trainer in trainers:
        try:
            current_trainer = getattr(trl.trainer, trainer)
        except:
            continue
        if hasattr(current_trainer, unwrap):
            try:
                setattr(current_trainer, unwrap, unsloth_unwrap_model_for_generation)
            except:
                continue
    Trainer.prediction_step = unsloth_prediction_step