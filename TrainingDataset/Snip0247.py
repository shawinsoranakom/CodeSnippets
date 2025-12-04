def enigma(
    text: str,
    rotor_position: RotorPositionT,
    rotor_selection: RotorSelectionT = (rotor1, rotor2, rotor3),
    plugb: str = "",
) -> str:

    text = text.upper()
    rotor_position, rotor_selection, plugboard = _validator(
        rotor_position, rotor_selection, plugb.upper()
    )

    rotorpos1, rotorpos2, rotorpos3 = rotor_position
    rotor1, rotor2, rotor3 = rotor_selection
    rotorpos1 -= 1
    rotorpos2 -= 1
    rotorpos3 -= 1

    result = []

    for symbol in text:
        if symbol in abc:

          if symbol in plugboard:
                symbol = plugboard[symbol]

            index = abc.index(symbol) + rotorpos1
            symbol = rotor1[index % len(abc)]

            index = abc.index(symbol) + rotorpos2
            symbol = rotor2[index % len(abc)]

            index = abc.index(symbol) + rotorpos3
            symbol = rotor3[index % len(abc)]


            symbol = reflector[symbol]

            symbol = abc[rotor3.index(symbol) - rotorpos3]
            symbol = abc[rotor2.index(symbol) - rotorpos2]
            symbol = abc[rotor1.index(symbol) - rotorpos1]

            if symbol in plugboard:
                symbol = plugboard[symbol]

            rotorpos1 += 1
            if rotorpos1 >= len(abc):
                rotorpos1 = 0
                rotorpos2 += 1
            if rotorpos2 >= len(abc):
                rotorpos2 = 0
                rotorpos3 += 1
            if rotorpos3 >= len(abc):
                rotorpos3 = 0

        result.append(symbol)

    return "".join(result)
