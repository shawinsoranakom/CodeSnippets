def test_init_weights_can_init_buffers(self):
        """Ensure that all buffers (persistent and non-persistent) are correctly taken into account in `_init_weights`"""
        config, _ = self.model_tester.prepare_config_and_inputs_for_common()

        # Usually, buffers are not initialized randomly (it's kind of the point of having a Buffer instead of a Parameter...)
        # However, some PositionalEmbedding modules have a `positional_embedding` buffer, initialized randomly with normal
        # distribution and std `config.scale` - set it at 0 here to avoid randomness
        if hasattr(config, "scale"):
            config.scale = 0
        for sub_key in config.sub_configs:
            subconfig = getattr(config, sub_key)
            if subconfig is not None and hasattr(subconfig, "scale"):
                subconfig.scale = 0

        for model_class in self.all_model_classes:
            # First, initialize the model directly with `__init__`, with the context manager making sure that we do
            # not run `initialiaze_weights()`, i.e. buffers are the same as in the modules's `__init__` initial definition
            with skip_weight_init():
                model_from_init = model_class(copy.deepcopy(config))
            # Second, initialize the model fully on meta device, then move everything to cpu and run `init_weights`
            with torch.device("meta"):
                model_from_meta_init = model_class(copy.deepcopy(config))
            # move everything randomly to cpu
            model_from_meta_init.to_empty(device="cpu")
            # Now, run all the inits
            model_from_meta_init.init_weights()

            buffers_from_init = dict(model_from_init.named_buffers())
            buffers_from_meta_init = dict(model_from_meta_init.named_buffers())

            self.assertEqual(
                sorted(buffers_from_init.keys()),
                sorted(buffers_from_meta_init.keys()),
                "The name of the buffers from each model should be the exact same",
            )

            # Buffers are not random usually, so everything must match exactly
            different_buffers = set()
            for k1, v1 in buffers_from_init.items():
                v2 = buffers_from_meta_init[k1]
                if not (v1 == v2).all():
                    different_buffers.add(k1)

            # Find the parent structure of the buffers that are different for explicit error messages
            unique_bad_module_traceback = set()
            for buffer in different_buffers.copy():
                buf_name, immediate_parent_class, pretrained_parent_class = find_parent_traceback(
                    buffer, model_from_init
                )
                # Add it to the traceback
                traceback = (
                    f"`{buf_name}` in module `{immediate_parent_class}` called from `{pretrained_parent_class}`\n"
                )
                unique_bad_module_traceback.add(traceback)

            unique_bad_module_traceback = "".join(unique_bad_module_traceback)
            self.assertTrue(
                len(different_buffers) == 0,
                f"The following buffers are not properly handled in `_init_weights()` (the model should be able to reinitialize "
                f"them correctly if the model is on meta device):\n{unique_bad_module_traceback}",
            )