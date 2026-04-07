def _clone(self, g):
        if isinstance(g, GEOM_PTR):
            return capi.geom_clone(g)
        else:
            return capi.geom_clone(g.ptr)