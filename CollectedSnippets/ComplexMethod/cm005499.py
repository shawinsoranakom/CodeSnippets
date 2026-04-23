def build_peft_weight_mapping(
    weight_conversions: list[WeightConverter | WeightRenaming] | None, adapter_name: str, peft_config=None
) -> list[WeightConverter | WeightRenaming]:
    # We iterate over all the operations of the original model and simply edit them to apply to the PEFT adapter when
    # appropriate.
    # Note: This function is used in PEFT, changing it requires coordination.
    if not weight_conversions:
        return []

    # strip "base_model.model" and add adapter name
    new_weight_conversions = [
        WeightRenaming("base_model.model.model.", "model."),
        WeightRenaming("base_model.model.", ""),
    ]

    prefixes = set()
    from peft.mapping import PEFT_TYPE_TO_PREFIX_MAPPING

    peft_type = getattr(peft_config, "peft_type", None)
    if peft_type in PEFT_TYPE_TO_PREFIX_MAPPING:
        prefixes.add(PEFT_TYPE_TO_PREFIX_MAPPING[peft_type])
    else:
        prefixes.update(PEFT_TYPE_TO_PREFIX_MAPPING.values())

    for prefix in sorted(prefixes):
        escaped_prefix = re.escape(prefix)
        new_weight_conversions.append(
            WeightRenaming(
                source_patterns=rf"({escaped_prefix}[^\.]*)",
                target_patterns=rf"\1.{adapter_name}",
            )
        )

    for orig_conversion in weight_conversions:
        if isinstance(orig_conversion, WeightRenaming):
            new_weight_conversions.append(orig_conversion)
            continue

        if len(orig_conversion.target_patterns) == 1 and orig_conversion.target_patterns[0].endswith("gate_up_proj"):
            # gate_up_proj requires both merging the experts and concatenating for the fusion of w1 and w3
            for lora in ("lora_A", "lora_B"):  # TODO: lora_embedding_A and lora_embedding_B
                # deal with operations
                peft_weight_operations = []
                for op in orig_conversion.operations:
                    if isinstance(op, Concatenate):
                        if lora == "lora_B":  # block diagonal concat
                            peft_weight_operations.append(PeftConcatenate(dim=op.dim))
                        else:  # normal concat + flatten
                            peft_weight_operations.append(op)
                            peft_weight_operations.append(FlattenDims(dims=(0, 1)))
                    elif isinstance(op, MergeModulelist):
                        peft_weight_operations.append(op)

                # TODO: this assumption may not hold for models != mixtral
                # For source, we capture the original weights + the lora weights
                new_source_patterns = []
                for pat in list(orig_conversion.source_patterns):
                    # we replace the weight pattern to colllect loras
                    pat = pat.rsplit(".", 1)[0]
                    # note: the source state_dict does *not* contain the adapter name
                    new_source_patterns.append(f"{pat}.{lora}.*")

                # the gate_up_proj is the innner PEFT ParamWrapper, so we need to use base_layer
                pat = orig_conversion.target_patterns[0]
                pat = pat.replace("gate_up_proj", "base_layer")
                # we make sure the target key is correct, add '.weight' because the parameter is targeted directly
                new_target_patterns = [f"{pat}.{lora}.{adapter_name}.weight"]

                # Instantiate a new object that correctly post process patterns if needed
                new_conversion = orig_conversion.__class__(
                    source_patterns=new_source_patterns,
                    target_patterns=new_target_patterns,
                    distributed_operation=orig_conversion.distributed_operation,
                    quantization_operation=orig_conversion.quantization_operation,
                    operations=peft_weight_operations,
                )
                new_weight_conversions.append(new_conversion)

        elif len(orig_conversion.target_patterns) == 1 and orig_conversion.target_patterns[0].endswith("down_proj"):
            # down_proj only requires merging of experts
            for lora in ("lora_A", "lora_B"):  # TODO: lora_embedding_A and lora_embedding_B
                peft_weight_operations = []
                for op in orig_conversion.operations:
                    if isinstance(op, MergeModulelist):
                        peft_weight_operations.append(op)
                        if lora == "lora_A":
                            peft_weight_operations.append(FlattenDims(dims=(0, 1)))
                        else:
                            peft_weight_operations.append(PermuteDims(dims=(2, 0, 1)))
                            peft_weight_operations.append(FlattenDims(dims=(0, 1)))
                            peft_weight_operations.append(Transpose(dim0=0, dim1=1))

                # TODO: this assumption may not hold for models != mixtral
                # For source, we capture the original weights + the lora weights
                new_source_patterns = []
                for pat in list(orig_conversion.source_patterns):
                    # we replace the weight pattern to colllect loras
                    pat = pat.rsplit(".", 1)[0]
                    # note: the source state_dict does *not* contain the adapter name
                    new_source_patterns.append(f"{pat}.{lora}.*")

                # the down_proj is the outer PEFT ParamWrapper, so we remove the prefix
                pat = orig_conversion.target_patterns[0]
                pat = pat.replace(".down_proj", "")
                # we make sure the target key is correct, add '.weight' because the parameter is targeted directly
                new_target_patterns = [f"{pat}.{lora}.{adapter_name}.weight"]

                # Instantiate a new object that correctly post process patterns if needed
                new_conversion = orig_conversion.__class__(
                    source_patterns=new_source_patterns,
                    target_patterns=new_target_patterns,
                    distributed_operation=orig_conversion.distributed_operation,
                    quantization_operation=orig_conversion.quantization_operation,
                    operations=peft_weight_operations,
                )
                new_weight_conversions.append(new_conversion)

    return new_weight_conversions