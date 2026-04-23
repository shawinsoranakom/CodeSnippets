def get_suggested_xfails(base, tests):
    result = []
    tests = [test[len(base) :] for test in tests if belongs_to_base(test, base)]

    base_tests = {remove_device_dtype(test) for test in tests}
    tests = set(tests)
    for base in base_tests:
        cpu_variant = base + "_cpu_float32"
        cuda_variant = base + "_cuda_float32"
        namespace, api, variant = parse_base(base)
        if namespace is not None:
            api = f"{namespace}.{api}"
        if cpu_variant in tests and cuda_variant in tests:
            result.append(f"xfail('{api}', '{variant}'),")
            continue
        if cpu_variant in tests:
            result.append(f"xfail('{api}', '{variant}', device_type='cpu'),")
            continue
        if cuda_variant in tests:
            result.append(f"xfail('{api}', '{variant}', device_type='cuda'),")
            continue
        result.append(f"skip('{api}', '{variant}',")
    return result