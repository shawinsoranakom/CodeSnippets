def __init__(self, degrees, translate=None, scale=None, shear=None):
        assert isinstance(degrees, numbers.Number), "degree should be a single number."
        assert degrees >= 0, "degree must be positive."
        self.degrees = degrees

        if translate is not None:
            assert (
                isinstance(translate, (tuple, list)) and len(translate) == 2
            ), "translate should be a list or tuple and it must be of length 2."
            for t in translate:
                if not (0.0 <= t <= 1.0):
                    raise ValueError("translation values should be between 0 and 1")
        self.translate = translate

        if scale is not None:
            assert (
                isinstance(scale, (tuple, list)) and len(scale) == 2
            ), "scale should be a list or tuple and it must be of length 2."
            for s in scale:
                if s <= 0:
                    raise ValueError("scale values should be positive")
        self.scale = scale

        if shear is not None:
            if isinstance(shear, numbers.Number):
                if shear < 0:
                    raise ValueError(
                        "If shear is a single number, it must be positive."
                    )
                self.shear = [shear]
            else:
                assert isinstance(shear, (tuple, list)) and (
                    len(shear) == 2
                ), "shear should be a list or tuple and it must be of length 2."
                self.shear = shear
        else:
            self.shear = shear