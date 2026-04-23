def is_pytorch_file(rel_filepath) -> bool:
    _deprecated("is_pytorch_file")
    if os.path.isabs(rel_filepath):
        raise AssertionError("rel_filepath must be a relative path")
    if rel_filepath.startswith("aten/"):
        if rel_filepath.startswith("aten/src/ATen/core/"):
            return False
        return True
    if rel_filepath.startswith("torch/"):
        return True
    if rel_filepath.startswith("third_party/nvfuser/"):
        return True
    if rel_filepath.startswith("third_party/fbgemm/"):
        return True
    if rel_filepath.startswith("third_party/mslk/"):
        return True
    if rel_filepath.startswith("tools/autograd/templates/"):
        return True
    if rel_filepath.startswith("test/cpp/c10d/"):
        return True
    return False