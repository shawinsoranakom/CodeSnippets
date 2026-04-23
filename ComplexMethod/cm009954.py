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