def __init__(self, *args: Dataset[_T_co], **kwargs: Dataset[_T_co]) -> None:
        if args:
            if kwargs:
                raise ValueError(
                    "Supported either ``tuple``- (via ``args``) or"
                    "``dict``- (via ``kwargs``) like input/output, but both types are given."
                )
            self._length = len(args[0])  # type: ignore[arg-type]
            if any(self._length != len(dataset) for dataset in args):  # type: ignore[arg-type]
                raise ValueError("Size mismatch between datasets")
            self.datasets = args
        elif kwargs:
            tmp = list(kwargs.values())
            self._length = len(tmp[0])  # type: ignore[arg-type]
            if any(self._length != len(dataset) for dataset in tmp):  # type: ignore[arg-type]
                raise ValueError("Size mismatch between datasets")
            self.datasets = kwargs
        else:
            raise ValueError("At least one dataset should be passed")