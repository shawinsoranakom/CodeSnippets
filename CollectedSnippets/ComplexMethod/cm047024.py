def check_valid_config(
    permute_x, permute_y, use_W1, fuse_mul_post = False, is_backward = False, verbose = False
):
    use_W2 = not use_W1

    if permute_x and permute_y:
        if verbose:
            print(f"Skipping test: {permute_x = } {permute_y = }")
        return False
    if use_W2 and permute_x:
        if verbose:
            print(f"Skipping test: {permute_x = } {use_W2 = }")
        return False
    if use_W1 and permute_y:
        if verbose:
            print(f"Skipping test: {permute_y = } {use_W1 = }")
        return False
    if fuse_mul_post and use_W1:
        if verbose:
            print(f"Skipping test: {fuse_mul_post = } {use_W1 = }")
        return False
    if is_backward and fuse_mul_post:
        if verbose:
            print(f"Skipping test: {fuse_mul_post = } {is_backward = }")
        return False

    return True