def test_can_use_safetensors(self):
        for model_class in self.all_model_classes:
            config, _ = self.model_tester.prepare_config_and_inputs_for_common()
            model_tied = model_class(config)
            with tempfile.TemporaryDirectory() as d:
                try:
                    model_tied.save_pretrained(d)
                except Exception as e:
                    raise Exception(f"Class {model_class.__name__} cannot be saved using safetensors: {e}")
                with self.subTest(model_class):
                    model_reloaded, infos = model_class.from_pretrained(d, output_loading_info=True)
                    # Checking the state dicts are correct
                    reloaded_state = model_reloaded.state_dict()
                    for k, v in model_tied.state_dict().items():
                        with self.subTest(f"{model_class.__name__}.{k}"):
                            torch.testing.assert_close(
                                v,
                                reloaded_state[k],
                                msg=lambda x: f"{model_class.__name__}: Tensor {k}: {x}.\n{v}\nvs\n{reloaded_state[k]}\n"
                                "This probably means that it was not set with the correct value when tying.",
                            )

                    # Checking the tensor sharing are correct on the new model (weights are properly tied in both cases)
                    ptrs = defaultdict(list)
                    for k, v in model_tied.state_dict().items():
                        ptrs[v.data_ptr()].append(k)

                    shared_ptrs = {k: v for k, v in ptrs.items() if len(v) > 1}

                    for shared_names in shared_ptrs.values():
                        reloaded_ptrs = {reloaded_state[k].data_ptr() for k in shared_names}
                        self.assertEqual(
                            len(reloaded_ptrs),
                            1,
                            f"The shared pointers are incorrect, found different pointers for keys {shared_names}. `__init__` and `from_pretrained` end up not tying the weights the same way.",
                        )

                    # Checking there was no complain of missing weights
                    self.assertEqual(
                        infos["missing_keys"],
                        set(),
                        "These keys were removed when serializing, and were not properly loaded by `from_pretrained`.",
                    )