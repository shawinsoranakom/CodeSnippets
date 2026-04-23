def _parse_combined_prompt(combined_prompt, dataset):
    # Find {...}
    possible_columns = re.findall(r"\{(.+?)\}", combined_prompt)
    dataset_columns = set(dataset.column_names)
    for column in possible_columns:
        if column not in dataset_columns:
            raise KeyError(
                f"Unsloth: Your prompt includes '{column}' but this does not exist in the dataset. "\
                f"Only allowed columns are {list(dataset_columns)}"
            )

    # Find [[...]]
    optional_prompts = list(re.finditer(r"\[\[.+?\]\]", combined_prompt, flags = re.DOTALL | re.MULTILINE))
    optional_prompts = [(x.span(), x.group(0)) for x in optional_prompts]

    final_optional_prompts = []
    if len(optional_prompts) != 0:
        # Add left
        left = optional_prompts[0]
        l = left[0][0]
        if l != 0: final_optional_prompts.append(combined_prompt[:l])

        # Add in between
        for left, right in zip(optional_prompts[:-1], optional_prompts[1:]):
            l, r = left[0][-1], right[0][0]
            final_optional_prompts.append(left)
            if l != r: final_optional_prompts.append(combined_prompt[l : r])
        final_optional_prompts.append(optional_prompts[-1])

        # Add right
        right = optional_prompts[-1]
        r = right[0][1]
        if r != len(combined_prompt): final_optional_prompts.append(combined_prompt[r:])
    else:
        # Just add in the entire string
        final_optional_prompts.append(combined_prompt)

    check_combined = "".join(x if type(x) is str else x[1] for x in final_optional_prompts)
    assert(combined_prompt == check_combined)

    return possible_columns, final_optional_prompts