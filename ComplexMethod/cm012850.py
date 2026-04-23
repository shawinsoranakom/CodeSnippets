def _load_from_state_dict(
        self,
        state_dict,
        prefix,
        local_metadata,
        strict,
        missing_keys,
        unexpected_keys,
        error_msgs,
    ):
        # Removing this function throws an error that the size of the loaded tensor does not match the original size
        # i.e., These buffers start out with numel 0 and become numel 1 once they have their first forward pass.
        local_state = ["scale", "zero_point"]
        for name in local_state:
            key = prefix + name
            if key in state_dict:
                val = state_dict[key]
                # Custom handling to allow loading scale and zero_point
                # of size N into uninitialized buffers of size 0. The
                # buffers are resized here, and the values are copied in
                # the default state_dict loading code of the parent.
                if name == "scale":
                    self.scale.resize_(val.shape)
                else:
                    if name != "zero_point":
                        raise AssertionError(
                            "Expected 'zero_point' but got different state key"
                        )
                    self.zero_point.resize_(val.shape)
                # For torchscript module we need to update the attributes here since we do not
                # call the `_load_from_state_dict` function defined module.py
                if torch.jit.is_scripting():
                    if name == "scale":
                        self.scale.copy_(val)
                    else:
                        if name != "zero_point":
                            raise AssertionError(
                                "Expected 'zero_point' but got different state key"
                            )
                        self.zero_point.copy_(val)
            elif strict:
                missing_keys.append(key)
        super()._load_from_state_dict(
            state_dict,
            prefix,
            local_metadata,
            strict,
            missing_keys,
            unexpected_keys,
            error_msgs,
        )