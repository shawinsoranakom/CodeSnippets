def _generate_func_supporting_param(param, dataset_type=("load", "fetch")):
    markers_fetch = FETCH_PYTEST_MARKERS.get(param, {})
    for name, obj in inspect.getmembers(sklearn.datasets):
        if not inspect.isfunction(obj):
            continue

        is_dataset_type = any([name.startswith(t) for t in dataset_type])
        is_support_param = param in inspect.signature(obj).parameters
        if is_dataset_type and is_support_param:
            # check if we should skip if we don't have network support
            marks = [
                pytest.mark.skipif(
                    condition=name.startswith("fetch") and _skip_network_tests(),
                    reason="Skip because fetcher requires internet network",
                )
            ]
            if name in markers_fetch:
                marks.append(markers_fetch[name])

            yield pytest.param(name, obj, marks=marks)