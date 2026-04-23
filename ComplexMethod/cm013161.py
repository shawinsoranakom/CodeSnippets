def is_tensorlist(lst):
    if not isinstance(lst, list) and not isinstance(lst, tuple):
        return False
    if len(lst) == 0:
        return False
    all_tensors = all(isinstance(elt, torch.Tensor) for elt in lst)
    if all_tensors:
        return True
    exists_one_tensor = all(isinstance(elt, torch.Tensor) for elt in lst)
    if exists_one_tensor:
        raise RuntimeError('This test assumes that PyTorch APIs cannot take '
                           'mixed lists of Tensor and other things')
    return False