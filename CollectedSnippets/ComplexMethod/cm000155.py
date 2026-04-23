def enigma(
    text: str,
    rotor_position: RotorPositionT,
    rotor_selection: RotorSelectionT = (rotor1, rotor2, rotor3),
    plugb: str = "",
) -> str:
    """
    The only difference with real-world enigma is that ``I`` allowed string input.
    All characters are converted to uppercase. (non-letter symbol are ignored)

    | How it works:
    | (for every letter in the message)

    - Input letter goes into the plugboard.
      If it is connected to another one, switch it.

    - Letter goes through ``3`` rotors.
      Each rotor can be represented as ``2`` sets of symbol, where one is shuffled.
      Each symbol from the first set has corresponding symbol in
      the second set and vice versa.

      example::

      | ABCDEFGHIJKLMNOPQRSTUVWXYZ | e.g. F=D and D=F
      | VKLEPDBGRNWTFCJOHQAMUZYIXS |

    - Symbol then goes through reflector (static rotor).
      There it is switched with paired symbol.
      The reflector can be represented as ``2`` sets, each with half of the alphanet.
      There are usually ``10`` pairs of letters.

      Example::

      | ABCDEFGHIJKLM | e.g. E is paired to X
      | ZYXWVUTSRQPON | so when E goes in X goes out and vice versa

    - Letter then goes through the rotors again

    - If the letter is connected to plugboard, it is switched.

    - Return the letter

    >>> enigma('Hello World!', (1, 2, 1), plugb='pictures')
    'KORYH JUHHI!'
    >>> enigma('KORYH, juhhi!', (1, 2, 1), plugb='pictures')
    'HELLO, WORLD!'
    >>> enigma('hello world!', (1, 1, 1), plugb='pictures')
    'FPNCZ QWOBU!'
    >>> enigma('FPNCZ QWOBU', (1, 1, 1), plugb='pictures')
    'HELLO WORLD'


    :param text: input message
    :param rotor_position: tuple with ``3`` values in range ``1``.. ``26``
    :param rotor_selection: tuple with ``3`` rotors
    :param plugb: string containing plugboard configuration (default ``''``)
    :return: en/decrypted string
    """

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

    # encryption/decryption process --------------------------
    for symbol in text:
        if symbol in abc:
            # 1st plugboard --------------------------
            if symbol in plugboard:
                symbol = plugboard[symbol]

            # rotor ra --------------------------
            index = abc.index(symbol) + rotorpos1
            symbol = rotor1[index % len(abc)]

            # rotor rb --------------------------
            index = abc.index(symbol) + rotorpos2
            symbol = rotor2[index % len(abc)]

            # rotor rc --------------------------
            index = abc.index(symbol) + rotorpos3
            symbol = rotor3[index % len(abc)]

            # reflector --------------------------
            # this is the reason you don't need another machine to decipher

            symbol = reflector[symbol]

            # 2nd rotors
            symbol = abc[rotor3.index(symbol) - rotorpos3]
            symbol = abc[rotor2.index(symbol) - rotorpos2]
            symbol = abc[rotor1.index(symbol) - rotorpos1]

            # 2nd plugboard
            if symbol in plugboard:
                symbol = plugboard[symbol]

            # moves/resets rotor positions
            rotorpos1 += 1
            if rotorpos1 >= len(abc):
                rotorpos1 = 0
                rotorpos2 += 1
            if rotorpos2 >= len(abc):
                rotorpos2 = 0
                rotorpos3 += 1
            if rotorpos3 >= len(abc):
                rotorpos3 = 0

        # else:
        #    pass
        #    Error could be also raised
        #    raise ValueError(
        #       'Invalid symbol('+repr(symbol)+')')
        result.append(symbol)

    return "".join(result)