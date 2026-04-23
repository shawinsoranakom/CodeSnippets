def mux(input0: int, input1: int, select: int) -> int:
    if all(i in (0, 1) for i in (input0, input1, select)):
        return input1 if select else input0
    raise ValueError("Inputs and select signal must be 0 or 1")
