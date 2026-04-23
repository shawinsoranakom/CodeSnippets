def convert_to_HWC(tensor, input_format):  # tensor: numpy array
    if len(set(input_format)) != len(input_format):
        raise AssertionError(f"You can not use the same dimension shordhand twice. \
            input_format: {input_format}")
    if len(tensor.shape) != len(input_format):
        raise AssertionError(f"size of input tensor and input format are different. \
        tensor shape: {tensor.shape}, input_format: {input_format}")
    input_format = input_format.upper()

    if len(input_format) == 4:
        index = [input_format.find(c) for c in "NCHW"]
        tensor_NCHW = tensor.transpose(index)
        tensor_CHW = make_grid(tensor_NCHW)
        return tensor_CHW.transpose(1, 2, 0)

    if len(input_format) == 3:
        index = [input_format.find(c) for c in "HWC"]
        tensor_HWC = tensor.transpose(index)
        if tensor_HWC.shape[2] == 1:
            tensor_HWC = np.concatenate([tensor_HWC, tensor_HWC, tensor_HWC], 2)
        return tensor_HWC

    if len(input_format) == 2:
        index = [input_format.find(c) for c in "HW"]
        tensor = tensor.transpose(index)
        tensor = np.stack([tensor, tensor, tensor], 2)
        return tensor