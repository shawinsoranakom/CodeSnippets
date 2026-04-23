def gen_data(special_op_lists, analysis_name):
    all_ops = get_ops_for_key(None)
    composite_ops = get_ops_for_key("CompositeImplicitAutograd")
    noncomposite_ops = all_ops - composite_ops
    with open("../../aten/src/ATen/native/native_functions.yaml") as f:
        ops = yaml.load(f.read(), Loader=yaml.CLoader)

    with open("annotated_ops") as f:
        annotated_ops = {a.strip(): b.strip() for a, b in csv.reader(f)}

    uniq_ops = []
    uniq_names = set()
    overload_types = defaultdict(list)
    cnt = 0
    for op in ops:
        func_str = op["func"]
        name = func_str[: func_str.index("(")]
        if "." in name:
            uniq_name = name[: name.index(".")]
            overload_types[name[name.index(".") + 1 :]].append(name)
        else:
            uniq_name = name
        op["name"] = uniq_name
        full_name = func_str[: func_str.index("(")]
        op["full_name"] = full_name
        ret_type = func_str[func_str.index("->") + 3 :]
        op["ret_type"] = ret_type
        cnt += 1
        if uniq_name in uniq_names:
            continue
        uniq_names.add(uniq_name)
        uniq_ops.append(op)

    def annotate_ops(ops, is_unique):
        categorization = defaultdict(int)
        for op in ops:
            if op["name"][-1] == "_":
                categorization["inplace"] += 1
                op["meta"] = "inplace"
                continue
            if not is_unique and "a!" in op["func"].lower():
                categorization["out"] += 1
                op["meta"] = "out"
                continue
            if "conv" in op["name"]:
                categorization["conv"] += 1
                op["meta"] = "conv"
                continue
            if "pool" in op["name"]:
                categorization["pool"] += 1
                op["meta"] = "pool"
                continue
            if "backward" in op["name"]:
                categorization["backward"] += 1
                op["meta"] = "backward"
                continue
            if op["name"][0] == "_" and op["name"][1] != "_":
                categorization["private"] += 1
                op["meta"] = "private"
                continue
            if "batch_norm" in op["name"]:
                categorization["batch_norm"] += 1
                op["meta"] = "batch_norm"
                continue
            if "Tensor" not in op["func"] or "Tensor" not in op["ret_type"]:
                categorization["non_tensor"] += 1
                op["meta"] = "non_tensor"
                continue
            if (
                "cudnn" in op["name"]
                or "mkldnn" in op["name"]
                or "miopen" in op["name"]
                or "native" in op["name"]
                or "thnn" in op["name"]
                or "slow" in op["name"]
            ):
                categorization["backend"] += 1
                op["meta"] = "backend"
                continue
            if op["name"] in annotated_ops:
                categorization["core"] += 1
                op["meta"] = "core " + annotated_ops[op["name"]]
                continue
            categorization["core"] += 1
            op["meta"] = "core unknown"
        return categorization

    annotate_ops(ops, is_unique=False)
    with open(f"{analysis_name}", "w") as f:
        for op in ops:
            info = [
                op["full_name"],
                op["meta"],
                op["full_name"] not in noncomposite_ops,
            ] + [check(op) for check in special_op_lists]
            f.write(",".join([str(i) for i in info]) + "\n")