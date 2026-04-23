def mmain() -> None:
    encoded = encode(input("-> ").strip().lower())
    print("Encoded: ", encoded)
    print("Decoded:", decode(encoded))
