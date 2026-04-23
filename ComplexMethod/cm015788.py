def convert_tensor_to_numpy(input: Any) -> Any:
    if isinstance(input, torch.Tensor):
        if torch.is_complex(input):
            # from complex to real representation
            input = torch.view_as_real(input)
        return input.detach().cpu().numpy()
    if isinstance(input, complex):
        return torch.view_as_real(torch.tensor(input)).detach().cpu().numpy()
    if isinstance(input, list):
        if len(input) == 0:
            return np.array((), dtype=np.int64)
        if any(isinstance(x, torch.Tensor) for x in input):
            # The list can be Optional[Tensor], e.g. [None, Tensor, None] etc.
            return [convert_tensor_to_numpy(x) for x in input]
        if isinstance(input[0], bool):
            return np.array(input, dtype=np.bool_)

        # Just a sequence of numbers
        if isinstance(input[0], int):
            return np.array(input, dtype=np.int64)
        if isinstance(input[0], float):
            return np.array(input)

    return input