def test_torch_export(self, atol=1e-4, rtol=1e-4):
        """
        Test if model can be exported with torch.export.export()

        Args:
            atol (`float`, *optional*, defaults to 1e-4): absolute tolerance for output comparison
            rtol (`float`, *optional*, defaults to 1e-4): relative tolerance for output comparison
        """

        if not self.test_torch_exportable:
            self.skipTest(reason="Model architecture is not torch exportable")

        with open(inspect.getfile(self.all_model_classes[0]), "r") as f:
            source_code = f.read()
            # Skip model if it uses a chunked attention implementation which is not torch exportable
            if "for q, k, v in zip(*splits)" in source_code:
                self.skipTest(reason="Model architecture uses chunked attention which is not torch exportable")
            # Skip MoEs that don't support batched_mm experts implementation
            if "for expert" in source_code and "use_experts_implementation" not in source_code:
                self.skipTest(reason="Model architecture uses eager MoE implementation which is not torch exportable")
            # Skip models that use get_rope_index which is not torch exportable
            if "get_rope_index" in source_code:
                self.skipTest(reason="Model architecture uses get_rope_index which is not torch exportable")

        def _is_pure_python_object(obj) -> bool:
            if isinstance(obj, (int, float, bool, str)) or obj is None:
                return True
            elif isinstance(obj, (list, tuple, set)):
                return all(_is_pure_python_object(o) for o in obj)
            elif isinstance(obj, dict):
                return all(_is_pure_python_object(o) for o in obj.values())
            else:
                return False

        def _get_leaf_tensors(obj) -> dict[str, torch.Tensor]:
            if _is_pure_python_object(obj):
                return {}
            elif isinstance(obj, torch.Tensor):
                return {"": obj}
            elif isinstance(obj, (list, tuple, set)):
                return _get_leaf_tensors(dict(enumerate(obj)))
            elif isinstance(obj, dict):
                leaf_tensors = {}
                for key, value in obj.items():
                    for sub_key, tensor in _get_leaf_tensors(value).items():
                        full_key = f"{key}.{sub_key}" if sub_key else str(key)
                        leaf_tensors[full_key] = tensor
                return leaf_tensors
            else:
                raise ValueError(f"Unexpected object type: {type(obj)}")

        def _prepare_for_export(model, inputs_dict):
            # we don't test outputing a cache class for now
            inputs_dict.pop("use_cache", None)
            # we don't test loss computation for now
            inputs_dict.pop("return_loss", None)
            # we don't test loss computation for now
            inputs_dict.pop("future_values", None)

            # set experts implementation to batched_mm for export
            if model._can_set_experts_implementation():
                model.set_experts_implementation("batched_mm")

            # set attention implementation to sdpa for export
            if model._can_set_attn_implementation() and model.config.model_type != "videomae":
                try:
                    model.set_attn_implementation("sdpa")
                except Exception as e:
                    print(
                        f"Could not set attention implementation to sdpa for {model} of type {model.config.model_type} : {e}"
                    )

            for module in model.modules():
                if hasattr(module, "config"):
                    # disable cache usage for every submodel
                    if hasattr(module.config, "use_cache"):
                        module.config.use_cache = False
                    # disable returning loss for every submodel
                    if hasattr(module.config, "return_loss"):
                        module.config.return_loss = False
                    # disable mamba kernels for every submodel (mamba, jamba)
                    if hasattr(module.config, "use_mamba_kernels"):
                        module.config.use_mamba_kernels = False
                # disable classifier cast for nllb-moe
                if hasattr(module, "_cast_classifier"):
                    module._cast_classifier = lambda *args, **kwargs: None
                # disable mamba mask update for ssms
                if hasattr(module, "_update_mamba_mask"):
                    module._update_mamba_mask = lambda attention_mask, *args, **kwargs: attention_mask
                if hasattr(module, "_update_linear_attn_mask"):
                    module._update_linear_attn_mask = lambda attention_mask, *args, **kwargs: attention_mask

            return model, inputs_dict

        for model_class in self.all_model_classes:
            with self.subTest(model_class.__name__):
                if model_class.__name__ == "VideoMAEForPreTraining":
                    # this model computes the loss unconditionally
                    continue

                if hasattr(self.model_tester, "prepare_config_and_inputs_for_model_class"):
                    config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_model_class(model_class)
                else:
                    config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
                inputs_dict = self._prepare_for_class(inputs_dict, model_class)
                set_config_for_less_flaky_test(config)
                model = model_class(config).eval().to(torch_device)
                set_model_for_less_flaky_test(model)

                # Prepare model and inputs for export
                model, inputs_dict = _prepare_for_export(model, inputs_dict)

                with torch.no_grad():
                    # Running the eager inference before the export to catch model/inputs comatibility issues, also sometimes after
                    # the export, the model used for export will return FakeTensors instead of real ones (torch compiler issue).
                    # This happens on cuda for example with (codegen, clvp, esm, gptj, levit, wav2vec2_bert and wav2vec2_conformer)
                    set_seed(1234)
                    eager_outputs = model(**copy.deepcopy(inputs_dict))
                    eager_outputs = _get_leaf_tensors(eager_outputs)
                    self.assertTrue(eager_outputs, "Eager outputs is empty.")

                try:
                    exported_program = torch.export.export(model, args=(), kwargs=copy.deepcopy(inputs_dict))
                except Exception as e:
                    raise e

                with torch.no_grad():
                    set_seed(1234)
                    exported_outputs = exported_program.module()(**copy.deepcopy(inputs_dict))
                    exported_outputs = _get_leaf_tensors(exported_outputs)
                    self.assertTrue(exported_outputs, "Exported outputs is empty.")

                # Check outputs closeness:
                torch.testing.assert_close(exported_outputs, eager_outputs, atol=atol, rtol=rtol)