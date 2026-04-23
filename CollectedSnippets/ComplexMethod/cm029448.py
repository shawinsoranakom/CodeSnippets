def compare_openai_inputs(
    left_payload: Any,
    right_payload: Any,
) -> OpenAIInputComparison:
    left_items = _extract_input_items(left_payload)
    right_items = _extract_input_items(right_payload)

    common_prefix_items = 0
    for index in range(min(len(left_items), len(right_items))):
        left_item = left_items[index]
        right_item = right_items[index]
        if left_item == right_item:
            common_prefix_items += 1
            continue

        nested_difference = _find_first_value_difference(left_item, right_item)
        nested_path = "" if nested_difference is None else nested_difference[0]
        path = f"input[{index}]"
        if nested_path:
            if nested_path.startswith("["):
                path = f"{path}{nested_path}"
            else:
                path = f"{path}.{nested_path}"

        left_value = left_item if nested_difference is None else nested_difference[1]
        right_value = right_item if nested_difference is None else nested_difference[2]

        return OpenAIInputComparison(
            common_prefix_items=common_prefix_items,
            left_item_count=len(left_items),
            right_item_count=len(right_items),
            difference=OpenAIInputDifference(
                item_index=index,
                path=path,
                left_summary=summarize_responses_input_item(index, left_item),
                right_summary=summarize_responses_input_item(index, right_item),
                left_value=left_value,
                right_value=right_value,
            ),
        )

    if len(left_items) != len(right_items):
        index = min(len(left_items), len(right_items))
        left_item = left_items[index] if index < len(left_items) else None
        right_item = right_items[index] if index < len(right_items) else None
        return OpenAIInputComparison(
            common_prefix_items=common_prefix_items,
            left_item_count=len(left_items),
            right_item_count=len(right_items),
            difference=OpenAIInputDifference(
                item_index=index,
                path=f"input[{index}]",
                left_summary=(
                    summarize_responses_input_item(index, left_item)
                    if left_item is not None
                    else f"{index:02d} <missing>"
                ),
                right_summary=(
                    summarize_responses_input_item(index, right_item)
                    if right_item is not None
                    else f"{index:02d} <missing>"
                ),
                left_value=left_item,
                right_value=right_item,
            ),
        )

    return OpenAIInputComparison(
        common_prefix_items=common_prefix_items,
        left_item_count=len(left_items),
        right_item_count=len(right_items),
        difference=None,
    )