def as_tensor(value):
                if torch.is_tensor(value):
                    return value

                # stack list of tensors if tensor_type is PyTorch (# torch.tensor() does not support list of tensors)
                if isinstance(value, (list, tuple)) and len(value) > 0 and torch.is_tensor(value[0]):
                    return torch.stack(value)

                # convert list of numpy arrays to numpy array (stack) if tensor_type is Numpy
                if isinstance(value, (list, tuple)) and len(value) > 0:
                    if isinstance(value[0], np.ndarray):
                        value = np.array(value)
                    elif (
                        isinstance(value[0], (list, tuple))
                        and len(value[0]) > 0
                        and isinstance(value[0][0], np.ndarray)
                    ):
                        value = np.array(value)
                if isinstance(value, np.ndarray):
                    return torch.from_numpy(value)
                else:
                    return torch.tensor(value)