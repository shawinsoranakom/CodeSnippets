def __post_init__(self) -> None:
        assert not isinstance(self.scalar, torch.SymInt), self.scalar
        if isinstance(self.size, tuple):
            for s in self.size:
                assert not isinstance(s, torch.SymInt), s
        if isinstance(self.stride, tuple):
            for s1 in self.stride:
                assert not isinstance(s1, torch.SymInt), s1