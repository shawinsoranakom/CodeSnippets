def match(self, event):
        # TODO: We should also check tensor identities
        if event.name != "aten::to":
            return False
        to_event = event
        if not event.children:
            return False
        event = event.children[-1]
        if event.name != "aten::_to_copy":
            return False
        if not event.children:
            return False
        event = event.children[-1]
        if event.name != "aten::copy_":
            return False
        # aten::copy_ should have the first 2 args dtype the same
        dtypes = input_dtypes(event)
        if len(dtypes) < 2:
            return False
        if dtypes[0] is None or dtypes[0] != dtypes[1]:
            return False
        event = to_event
        # Up one level
        event = event.parent
        if event is None:
            return False
        # Check if we have a aten::fill_ in previous leaf
        event = self.prev_of(event)
        if event is None:
            return False
        while event.children:
            event = event.children[-1]
            # aten::zero_ is a special optimization case where fill_ is not called
            if event.name in self.init_ops:
                return True
        return event.name in self.init_ops