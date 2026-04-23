def persistent_id(self, obj):
        if isinstance(obj, torch.Tensor):
            self.tensors.append(obj)
            return ""
        # Since we just want to extract tensors, we don't mind if an object is
        # unpicklable if it doesn't contain tensors, as we can just ignore/skip
        # it. To play it safe, we only do so for common objects that we're sure
        # don't contain tensors. Feel free to add new types here. Note also that
        # even if a type isn't listed here this won't block users, since they
        # can just add a __getstate__ or __reduce__ method to their class.
        if isinstance(obj, LockType):
            return ""
        # Futures and RRefs don't technically contain a value, they just offer
        # the means to access a value.
        if isinstance(obj, CFuture) or is_rref_instance(obj):
            return ""
        if isinstance(obj, CAwait):
            return ""
        if isinstance(obj, torch.cuda.Event):
            return ""
        if isinstance(obj, threading.Thread):
            return ""
        return None