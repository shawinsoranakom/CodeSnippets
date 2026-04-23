def equal_ref(qX, qX2):
            if qX.qscheme() != qX2.qscheme():
                return False
            if qX.shape != qX2.shape:
                return False
            if qX.dtype != qX2.dtype:
                return False
            if qX.qscheme() == torch.per_tensor_affine:
                if qX.q_scale() != qX2.q_scale():
                    return False
                if qX.q_zero_point() != qX2.q_zero_point():
                    return False
            elif qX.qscheme() == torch.per_channel_affine:
                if (qX.q_per_channel_scales() !=
                   qX2.q_per_channel_scales()).any():
                    return False
                if (qX.q_per_channel_zero_points() !=
                   qX2.q_per_channel_zero_points()).any():
                    return False
            else:
                raise NotImplementedError("Don't know what to do with",
                                          qX.qscheme())
            if (qX.int_repr().to(float) != qX2.int_repr().to(float)).any():
                return False
            return True