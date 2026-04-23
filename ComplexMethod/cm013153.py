def __init__(self, *args, device_type="all"):
        if len(args) > 0 and isinstance(args[0], (list, tuple)):
            for arg in args:
                if not isinstance(arg, (list, tuple)):
                    raise AssertionError(
                        "When one dtype variant is a tuple or list, "
                        "all dtype variants must be. "
                        f"Received non-list non-tuple dtype {str(arg)}"
                    )
                if not all(isinstance(dtype, torch.dtype) for dtype in arg):
                    raise AssertionError(f"Unknown dtype in {str(arg)}")
        else:
            if not all(isinstance(arg, torch.dtype) for arg in args):
                raise AssertionError(f"Unknown dtype in {str(args)}")

        self.args = args
        self.device_type = device_type