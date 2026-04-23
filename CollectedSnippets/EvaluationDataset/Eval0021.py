def test_end_to_end(msg: str = "Hello, this is a modified Caesar cipher") -> str:

    cip1 = ShuffledShiftCipher()
    return cip1.decrypt(cip1.encrypt(msg))
