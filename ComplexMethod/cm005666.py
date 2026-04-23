def wrapper(self, *args, **kwargs):
            # Pop it so that internal modules always return a dict even if False is requested
            return_dict = kwargs.pop("return_dict", getattr(self.config, "return_dict", True))

            # _can_record_outputs is None by default
            capturable_flags = _CAN_RECORD_REGISTRY.get(str(self.__class__)) or {}
            recordable_keys = {
                f"output_{k}": kwargs.get(f"output_{k}", getattr(self.config, f"output_{k}", False))
                for k in capturable_flags
            }
            # For BC as cross-attentions used to be captured with `output_attentions`
            if "cross_attentions" in capturable_flags:
                recordable_keys["output_cross_attentions"] = kwargs.get(
                    "output_attentions", getattr(self.config, "output_attentions", False)
                )
            # The sam model variants need this annoying exception as well...
            if "mask_decoder_attentions" in capturable_flags:
                recordable_keys["output_mask_decoder_attentions"] = kwargs.get(
                    "output_attentions", getattr(self.config, "output_attentions", False)
                )

            collected_outputs = {k.replace("output_", ""): [] for k, v in recordable_keys.items() if v}
            # Make sure hooks are installed if we need to collect outputs
            if len(collected_outputs) > 0:
                maybe_install_capturing_hooks(self)
            # Let's activate the output collector hooks if needed!
            output_token = _active_collector.set(collected_outputs)

            # Run the forward
            try:
                outputs = func(self, *args, **kwargs)
            # Reset the states
            finally:
                _active_collector.reset(output_token)

            # Inject collected outputs into model output (return everything as tuples for BC)
            for key in collected_outputs:
                if key == "hidden_states":
                    if not tie_last_hidden_states:
                        pass
                    elif hasattr(outputs, "vision_hidden_states"):
                        collected_outputs[key] = collected_outputs[key][:-1]
                        collected_outputs[key].append(outputs.vision_hidden_states)
                    elif hasattr(outputs, "last_hidden_state"):
                        collected_outputs[key] = collected_outputs[key][:-1]
                        collected_outputs[key].append(outputs.last_hidden_state)

                    outputs[key] = tuple(collected_outputs[key])
                elif key == "attentions":
                    # In this case, the second item are cross attentions
                    if isinstance(capturable_flags[key], list) and len(capturable_flags[key]) == 2:
                        outputs[key] = tuple(collected_outputs[key][0::2])
                        outputs["cross_" + key] = tuple(collected_outputs[key][1::2])
                    else:
                        outputs[key] = tuple(collected_outputs[key])
                else:
                    outputs[key] = tuple(collected_outputs[key])

            if return_dict is False:
                outputs = outputs.to_tuple()

            return outputs