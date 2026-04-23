def __init__(self):
        super().__init__()

        self.zeros = {"o", "oh", "zero"}
        # fmt: off
        self.ones = {
            name: i
            for i, name in enumerate(
                ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"],
                start=1,
            )
        }
        # fmt: on
        self.ones_plural = {
            "sixes" if name == "six" else name + "s": (value, "s") for name, value in self.ones.items()
        }
        self.ones_ordinal = {
            "zeroth": (0, "th"),
            "first": (1, "st"),
            "second": (2, "nd"),
            "third": (3, "rd"),
            "fifth": (5, "th"),
            "twelfth": (12, "th"),
            **{
                name + ("h" if name.endswith("t") else "th"): (value, "th")
                for name, value in self.ones.items()
                if value > 3 and value != 5 and value != 12
            },
        }
        self.ones_suffixed = {**self.ones_plural, **self.ones_ordinal}

        self.tens = {
            "twenty": 20,
            "thirty": 30,
            "forty": 40,
            "fifty": 50,
            "sixty": 60,
            "seventy": 70,
            "eighty": 80,
            "ninety": 90,
        }
        self.tens_plural = {name.replace("y", "ies"): (value, "s") for name, value in self.tens.items()}
        self.tens_ordinal = {name.replace("y", "ieth"): (value, "th") for name, value in self.tens.items()}
        self.tens_suffixed = {**self.tens_plural, **self.tens_ordinal}

        self.multipliers = {
            "hundred": 100,
            "thousand": 1_000,
            "million": 1_000_000,
            "billion": 1_000_000_000,
            "trillion": 1_000_000_000_000,
            "quadrillion": 1_000_000_000_000_000,
            "quintillion": 1_000_000_000_000_000_000,
            "sextillion": 1_000_000_000_000_000_000_000,
            "septillion": 1_000_000_000_000_000_000_000_000,
            "octillion": 1_000_000_000_000_000_000_000_000_000,
            "nonillion": 1_000_000_000_000_000_000_000_000_000_000,
            "decillion": 1_000_000_000_000_000_000_000_000_000_000_000,
        }
        self.multipliers_plural = {name + "s": (value, "s") for name, value in self.multipliers.items()}
        self.multipliers_ordinal = {name + "th": (value, "th") for name, value in self.multipliers.items()}
        self.multipliers_suffixed = {**self.multipliers_plural, **self.multipliers_ordinal}
        self.decimals = {*self.ones, *self.tens, *self.zeros}

        self.preceding_prefixers = {
            "minus": "-",
            "negative": "-",
            "plus": "+",
            "positive": "+",
        }
        self.following_prefixers = {
            "pound": "£",
            "pounds": "£",
            "euro": "€",
            "euros": "€",
            "dollar": "$",
            "dollars": "$",
            "cent": "¢",
            "cents": "¢",
        }
        self.prefixes = set(list(self.preceding_prefixers.values()) + list(self.following_prefixers.values()))
        self.suffixers = {
            "per": {"cent": "%"},
            "percent": "%",
        }
        self.specials = {"and", "double", "triple", "point"}

        self.words = {
            key
            for mapping in [
                self.zeros,
                self.ones,
                self.ones_suffixed,
                self.tens,
                self.tens_suffixed,
                self.multipliers,
                self.multipliers_suffixed,
                self.preceding_prefixers,
                self.following_prefixers,
                self.suffixers,
                self.specials,
            ]
            for key in mapping
        }
        self.literal_words = {"one", "ones"}