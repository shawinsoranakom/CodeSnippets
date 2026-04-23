def can_use_int_matmul(x1, x2):
        # torch._int_mm only accepts the following conditions:
        # 1. cuda
        # 2. both inputs must have int8 dtype
        # 3. both inputs must be 2d
        # 4. x1.shape must be [>16, >= 16 and a multiplier of 8]
        # 5. x2.shape must be [>= 16 and a multiplier of 8, multiplier of 8]
        if get_device() != "cuda":
            return False
        if x1_dtype != "int8" or x2_dtype != "int8":
            return False
        x1_shape = x1.shape
        x2_shape = x2.shape
        if x1.ndim != 2 or x2.ndim != 2:
            return False
        if x1_shape[0] <= 16 or x1_shape[1] < 16 or x1_shape[1] % 8 != 0:
            return False
        if x2_shape[0] < 16 or x2_shape[0] % 8 != 0 or x2_shape[1] % 8 != 0:
            return False
        return True