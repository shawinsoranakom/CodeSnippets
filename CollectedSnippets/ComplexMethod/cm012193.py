def _op_not_broadcasting_with_conv(weight_tensor, other_tensor):
        # According to opDoesNotBroadCastWithConv of frozen_conv_folding.cpp
        weight_shape = weight_tensor.shape
        other_shape = other_tensor.shape
        if len(weight_shape) < len(other_shape):
            return False
        if len(weight_shape) == len(other_shape) + 1:
            # weight shape is [o, i, *], other_shape is [o, 1...].
            for i in reversed(range(len(other_shape))):
                if i == 0 and weight_shape[0] == other_shape[i]:
                    continue
                if other_shape[i] != 1:
                    return False
        else:
            # weight shape is [o, i, *], other_shape is [1, i, *]
            for i in reversed(range(len(other_shape))):
                if i == 1 and weight_shape[0] == other_shape[i]:
                    continue
                if other_shape[i] != 1:
                    return False
        return True