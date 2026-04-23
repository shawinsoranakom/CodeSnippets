def pytest_collection_modifyitems(config, items):
    has_multiple_devices = False

    openvino_skipped_tests = []
    if backend() == "openvino":
        with open(
            "keras/src/backend/openvino/excluded_concrete_tests.txt", "r"
        ) as file:
            openvino_skipped_tests = file.readlines()
            # it is necessary to check if stripped line is not empty
            # and exclude such lines
            openvino_skipped_tests = [
                line.strip() for line in openvino_skipped_tests if line.strip()
            ]

    if backend() == "jax":
        import jax

        has_multiple_devices = jax.device_count() > 1

    requires_trainable_backend = pytest.mark.skipif(
        backend() in ["numpy", "openvino"],
        reason="Trainer not implemented for NumPy and OpenVINO backend.",
    )
    requires_multiple_devices = (
        None
        if has_multiple_devices
        else pytest.mark.skip(reason="Requires multiple devices")
    )

    for item in items:
        if "requires_trainable_backend" in item.keywords:
            item.add_marker(requires_trainable_backend)
        if requires_multiple_devices and "multi_device" in item.keywords:
            item.add_marker(requires_multiple_devices)

        # also, skip concrete tests for openvino, listed in the special file
        # this is more granular mechanism to exclude tests rather
        # than using --ignore option
        for skipped_test in openvino_skipped_tests:
            if skipped_test in item.nodeid:
                item.add_marker(
                    skip_if_backend(
                        "openvino",
                        "Not supported operation by openvino backend",
                    )
                )