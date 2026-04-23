def __init__(
        self,
        in_features: int,
        n_classes: int,
        cutoffs: Sequence[int],
        div_value: float = 4.0,
        head_bias: bool = False,
        device=None,
        dtype=None,
    ) -> None:
        factory_kwargs = {"device": device, "dtype": dtype}
        super().__init__()

        cutoffs = list(cutoffs)

        if len(cutoffs) == 0:
            raise ValueError("cutoffs should be a sequence of length larger than 0")

        if (
            (cutoffs != sorted(cutoffs))
            or (min(cutoffs) <= 0)
            or (max(cutoffs) > (n_classes - 1))
            or (len(set(cutoffs)) != len(cutoffs))
            or any(int(c) != c for c in cutoffs)
        ):
            raise ValueError(
                "cutoffs should be a sequence of unique, positive "
                "integers sorted in an increasing order, where "
                "each value is between 1 and n_classes-1"
            )

        self.in_features = in_features
        self.n_classes = n_classes
        self.cutoffs = cutoffs + [n_classes]
        self.div_value = div_value
        self.head_bias = head_bias

        self.shortlist_size = self.cutoffs[0]
        self.n_clusters = len(self.cutoffs) - 1
        self.head_size = self.shortlist_size + self.n_clusters

        self.head = Linear(
            self.in_features, self.head_size, bias=self.head_bias, **factory_kwargs
        )
        self.tail = ModuleList()

        for i in range(self.n_clusters):
            hsz = int(self.in_features // (self.div_value ** (i + 1)))
            osz = self.cutoffs[i + 1] - self.cutoffs[i]

            projection = Sequential(
                Linear(self.in_features, hsz, bias=False, **factory_kwargs),
                Linear(hsz, osz, bias=False, **factory_kwargs),
            )

            self.tail.append(projection)