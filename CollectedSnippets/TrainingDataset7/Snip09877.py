def __init__(self, oid, context):
            super().__init__(oid, context)
            self.orig_loader = orig_tz_loader_cls(oid, context)