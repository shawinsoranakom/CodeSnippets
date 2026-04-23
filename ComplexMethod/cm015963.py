def write_test_to_test_class(
    unit_test_class, test_params_dict, test_instance_class, parity_table, devices
):
    if not is_torch_nn_functional_test(test_params_dict):
        raise AssertionError("Expected torch.nn.functional test")

    if not (
        "cpp_options_args" in test_params_dict
        or "cpp_function_call" in test_params_dict
    ):
        raise AssertionError(
            "To enable C++ API parity test, "
            "`cpp_options_args` or `cpp_function_call` entry must be present in test params dict:\n"
            f"{pprint.pformat(test_params_dict)}. \n"
            "If you are interested in adding the C++ API parity test, please see:\n"
            "NOTE [How to check NN module / functional API parity between Python and C++ frontends]. \n"
            "If not, please add `test_cpp_api_parity=False` to the test params dict and file an issue about this."
        )

    if (
        "cpp_options_args" in test_params_dict
        and "cpp_function_call" in test_params_dict
    ):
        raise AssertionError(
            "Only one of `cpp_options_args` and `cpp_function_call` entries "
            f"should be present in test params dict:\n{pprint.pformat(test_params_dict)}"
        )

    functional_name = compute_functional_name(test_params_dict)

    if not hasattr(torch.nn.functional, functional_name):
        raise AssertionError(
            f"`torch.nn.functional` doesn't have function `{functional_name}`. "
            f"(Discovered while processing\n{pprint.pformat(test_params_dict)}.)"
        )

    functional_full_name = "F::" + functional_name

    if functional_full_name not in parity_table["torch::nn::functional"]:
        raise AssertionError(
            f"Please add `{functional_full_name}` entry to `torch::nn::functional` "
            "section of `test/cpp_api_parity/parity-tracker.md`. "
            f"(Discovered while processing\n{pprint.pformat(test_params_dict)}.)"
        )

    for device in devices:
        test_params = process_test_params_for_functional(
            test_params_dict=test_params_dict,
            device=device,
            test_instance_class=test_instance_class,
        )
        try_remove_folder(test_params.cpp_tmp_folder)
        unit_test_name = (
            f"test_torch_nn_functional_{test_params.functional_variant_name}"
        )
        unit_test_class.functional_test_params_map[unit_test_name] = test_params

        def test_fn(self):
            test_forward(
                unit_test_class=self,
                test_params=unit_test_class.functional_test_params_map[
                    self._testMethodName
                ],
            )

        test_fn = decorate_test_fn(
            test_fn=test_fn,
            test_cuda=test_params_dict.get("test_cuda", True),
            has_impl_parity=parity_table["torch::nn::functional"][functional_full_name][
                0
            ]
            and test_params_dict.get("has_parity", True),
            device=device,
        )

        add_test(unit_test_class, unit_test_name, test_fn)