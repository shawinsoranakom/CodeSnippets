def jumpy():
    # This won't actually run (but that's OK, we only disassemble it)
    for i in range(10):
        print(i)
        if i < 4:
            continue
        if i > 6:
            break
    else:
        print("I can haz else clause?")
    while i:
        print(i)
        i -= 1
        if i > 6:
            continue
        if i < 4:
            break
    else:
        print("Who let lolcatz into this test suite?")
    try:
        1 / 0
    except ZeroDivisionError:
        print("Here we go, here we go, here we go...")
    else:
        with i as dodgy:
            print("Never reach this")
    finally:
        print("OK, now we're done")