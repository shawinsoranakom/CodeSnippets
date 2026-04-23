def from_hf_inputs(
        hf_inputs: "BatchFeature",
        config_by_key: Mapping[str, MultiModalFieldConfig],
    ):
        # NOTE: This skips fields in `hf_inputs` that are not in `config_by_key`
        # We assume that those fields are not used in vLLM
        elems_by_key = dict[str, Sequence[MultiModalFieldElem]]()
        keys_by_modality = defaultdict[str, set[str]](set)
        for key, config in config_by_key.items():
            batch = hf_inputs.get(key)
            if batch is not None:
                elems = config.build_elems(key, batch)
                if len(elems) > 0:
                    elems_by_key[key] = elems
                    keys_by_modality[config.modality].add(key)

        items_by_modality = dict[str, list[MultiModalKwargsItem]]()
        for modality, keys in keys_by_modality.items():
            elems_in_modality = {k: elems_by_key[k] for k in keys}
            batch_sizes = {k: len(v) for k, v in elems_in_modality.items()}

            if len(set(batch_sizes.values())) > 1:
                raise ValueError(
                    f"Cannot merge different batch sizes for {modality=}! "
                    f"Found: {batch_sizes=}"
                )

            batch_size = next(iter(batch_sizes.values()))
            items_by_modality[modality] = [
                MultiModalKwargsItem({k: v[i] for k, v in elems_in_modality.items()})
                for i in range(batch_size)
            ]

        return MultiModalKwargsItems(items_by_modality)