def __repr__(self):
        spec = [
            (f"dtype={str(self.dtype)}") if self.dtype else "",
            (f"shape={str(self.shape)}") if self.shape else "",
            (f"ndim={str(self.ndim)}") if self.ndim else "",
            (f"max_ndim={str(self.max_ndim)}") if self.max_ndim else "",
            (f"min_ndim={str(self.min_ndim)}") if self.min_ndim else "",
            (f"axes={str(self.axes)}") if self.axes else "",
        ]
        return f"InputSpec({', '.join(x for x in spec if x)})"