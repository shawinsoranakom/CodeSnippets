def recursively_load_weights(orig_dict, hf_model, model_name):
    unused_weights = []

    if model_name not in ["dac_16khz", "dac_24khz", "dac_44khz"]:
        raise ValueError(f"Unsupported model: {model_name}")

    for name, value in orig_dict.items():
        is_used = False
        for key, mapped_key in MAPPING.items():
            regex = re.compile(key)
            if regex.search(name):
                if len(mapped_key) == 1:
                    if mapped_key[0][0] == "q":
                        mapped_key = ".".join(name.split(".")[:-1])
                    else:
                        mapped_key = mapped_key[0]
                elif len(mapped_key) == 3:
                    integers = re.findall(r"\b\d+\b", name)
                    if mapped_key[0][0] == "d":
                        mapped_key = f"{mapped_key[0]}.{str(int(integers[0]) - 1)}.{mapped_key[1]}{str(int(integers[1]) - 1)}.{mapped_key[2]}"
                    else:
                        mapped_key = f"{mapped_key[0]}.{str(int(integers[0]) - 1)}.{mapped_key[1]}{str(int(integers[1]) + 1)}.{mapped_key[2]}"
                elif len(mapped_key) == 2:
                    integers = re.findall(r"\b\d+\b", name)
                    mapped_key = f"{mapped_key[0]}.{str(int(integers[0]) - 1)}.{mapped_key[1]}"

                is_used = True
                if "weight_g" in name:
                    weight_type = "weight_g"
                elif "weight_v" in name:
                    weight_type = "weight_v"
                elif "bias" in name:
                    weight_type = "bias"
                elif "alpha" in name:
                    weight_type = "alpha"
                elif "weight" in name:
                    weight_type = "weight"
                set_recursively(hf_model, mapped_key, value, name, weight_type)

        if not is_used:
            unused_weights.append(name)

    print(list(set(unused_weights)))

    logger.warning(f"Unused weights: {unused_weights}")