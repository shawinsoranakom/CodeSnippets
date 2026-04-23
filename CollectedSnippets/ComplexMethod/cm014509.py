def main() -> None:
    args = parse_args()
    arc_yaml = Path(__file__).resolve().parent.parent / "arc.yaml"
    mapping = load_mapping(arc_yaml)

    matrix = yaml.safe_load(args.matrix)
    if not matrix:
        set_output("test-matrix", args.matrix)
        return

    entries = matrix.get("include", [])
    if not entries:
        set_output("test-matrix", json.dumps(matrix))
        return

    # TODO(huydo): onnxruntime uses hardware_concurrency() to size its thread
    # pool, which sees all host CPUs (e.g., 192) on ARC k8s instead of the
    # container's cpuset (e.g., 16). This causes pthread_setaffinity_np errors.
    # Skip onnx tests on ARC until the onnxruntime session options are fixed to
    # use cgroup-aware CPU counts.
    excluded_configs = {"onnx"}
    filtered = []
    for entry in entries:
        if entry.get("config") in excluded_configs:
            print(f"Excluding config '{entry['config']}' from ARC test matrix")
            continue
        filtered.append(entry)
    matrix["include"] = filtered

    for entry in filtered:
        if "runner" not in entry:
            continue
        clean = strip_prefix(entry["runner"].strip(), args.prefix)
        if clean not in mapping:
            print(f"error: no ARC runner found for '{clean}'", file=sys.stderr)
            sys.exit(1)
        mapped = mapping[clean]
        # Passthrough runners (e.g. linux.rocm.gpu.2, linux.idc.xpu) are not
        # OSDC-managed so they keep their original label without the prefix.
        entry["runner"] = mapped if mapped == clean else args.prefix + mapped

    set_output("test-matrix", json.dumps(matrix))