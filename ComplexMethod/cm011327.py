def create_default_global_save_plan(
    all_plans: list[SavePlan],
    rewrite_index_hints: bool = True,
) -> tuple[list[SavePlan], Metadata]:
    """
    Create the global plan and metadata used by DefaultSavePlanner.

    Metadata is produced by concatenating the metadata of all ``WriteItem`` from the supplied plans.

    The only global planning change is to update index hints in all ``MetadataIndex`` objects if
    ``rewrite_index_hints`` is True.
    """
    md: dict[str, STORAGE_TYPES] = {}
    new_plans = []
    for plan in all_plans:
        new_items = []
        for item in plan.items:
            if item.type != WriteItemType.SHARD:
                if item.index.fqn in md:
                    raise AssertionError("item.index.fqn not in md")

            if item.type == WriteItemType.BYTE_IO:
                md[item.index.fqn] = BytesStorageMetadata()
                new_items.append(item)
            else:
                if item.tensor_data is None:
                    raise AssertionError("item.tensor_data is not None")
                tensor_md = cast(
                    TensorStorageMetadata,
                    md.setdefault(
                        item.index.fqn,
                        TensorStorageMetadata(
                            properties=item.tensor_data.properties,
                            size=item.tensor_data.size,
                            chunks=[],
                        ),
                    ),
                )
                new_item = item
                if rewrite_index_hints:
                    new_index = dataclasses.replace(
                        item.index, index=len(tensor_md.chunks)
                    )
                    new_item = dataclasses.replace(item, index=new_index)
                new_items.append(new_item)

                if item.tensor_data.chunk is None:
                    raise AssertionError(f"""
                    Cannot create MD for tensor without bounds.
                    FQN: {item.index.fqn}
                """)
                tensor_md.chunks.append(item.tensor_data.chunk)
        new_plans.append(dataclasses.replace(plan, items=new_items))
    return (new_plans, Metadata(md))