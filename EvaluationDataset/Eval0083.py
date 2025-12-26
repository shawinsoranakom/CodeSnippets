class NumberingSystem(Enum):
    SHORT = (
        (15, "quadrillion"),
        (12, "trillion"),
        (9, "billion"),
        (6, "million"),
        (3, "thousand"),
        (2, "hundred"),
    )

    LONG = (
        (15, "billiard"),
        (9, "milliard"),
        (6, "million"),
        (3, "thousand"),
        (2, "hundred"),
    )

    INDIAN = (
        (14, "crore crore"),
        (12, "lakh crore"),
        (7, "crore"),
        (5, "lakh"),
        (3, "thousand"),
        (2, "hundred"),
    )

    @classmethod
    def max_value(cls, system: str) -> int:

        match system_enum := cls[system.upper()]:
            case cls.SHORT:
                max_exp = system_enum.value[0][0] + 3
            case cls.LONG:
                max_exp = system_enum.value[0][0] + 6
            case cls.INDIAN:
                max_exp = 19
            case _:
                raise ValueError("Invalid numbering system")
        return 10**max_exp - 1
