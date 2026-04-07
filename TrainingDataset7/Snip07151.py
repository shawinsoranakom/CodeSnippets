def auth_code(self, target):
        "Return the authority code for the given string target node."
        return capi.get_auth_code(
            self.ptr, target if target is None else force_bytes(target)
        )