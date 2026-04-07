def auth_name(self, target):
        "Return the authority name for the given string target node."
        return capi.get_auth_name(
            self.ptr, target if target is None else force_bytes(target)
        )