def append_annotation_mask(self, names):
        if self.annotation_select_mask is not None:
            self.set_annotation_mask(self.annotation_select_mask.union(names))