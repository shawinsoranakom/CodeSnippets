def _masked_tensor_str(data, mask, formatter):
    if data.layout in {torch.sparse_coo, torch.sparse_csr}:
        data = data.to_dense()
        mask = mask.to_dense()
    if data.dim() == 1:
        formatted_elements = [
            formatter.format(d.item()) if isinstance(d.item(), float) else str(d.item())
            for d in data
        ]
        max_len = max(8 if x[1] else len(x[0]) for x in zip(formatted_elements, ~mask))
        return (
            "["
            + ", ".join(
                [
                    "--".rjust(max_len) if m else e
                    for (e, m) in zip(formatted_elements, ~mask)
                ]
            )
            + "]"
        )
    sub_strings = [_masked_tensor_str(d, m, formatter) for (d, m) in zip(data, mask)]
    sub_strings = ["\n".join(["  " + si for si in s.split("\n")]) for s in sub_strings]
    return "[\n" + ",\n".join(sub_strings) + "\n]"