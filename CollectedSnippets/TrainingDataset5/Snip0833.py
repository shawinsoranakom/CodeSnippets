def __post_init__(self) -> None:
    if not isinstance(self.length, (int, float)) or self.length <= 0:
        raise TypeError("length must be a positive numeric value.")
    if not isinstance(self.angle, Angle):
        raise TypeError("angle must be an Angle object.")
    if not isinstance(self.next_side, (Side, NoneType)):
        raise TypeError("next_side must be a Side or None.")
