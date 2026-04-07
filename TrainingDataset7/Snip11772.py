def apply_bilateral_transforms(self, value):
        for transform in self.bilateral_transforms:
            value = transform(value)
        return value