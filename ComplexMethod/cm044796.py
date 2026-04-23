def hangul_number(num, sino=True):
    """Reference https://github.com/Kyubyong/g2pK"""
    num = re.sub(",", "", num)

    if num == "0":
        return "영"
    if not sino and num == "20":
        return "스무"

    digits = "123456789"
    names = "일이삼사오육칠팔구"
    digit2name = {d: n for d, n in zip(digits, names)}

    modifiers = "한 두 세 네 다섯 여섯 일곱 여덟 아홉"
    decimals = "열 스물 서른 마흔 쉰 예순 일흔 여든 아흔"
    digit2mod = {d: mod for d, mod in zip(digits, modifiers.split())}
    digit2dec = {d: dec for d, dec in zip(digits, decimals.split())}

    spelledout = []
    for i, digit in enumerate(num):
        i = len(num) - i - 1
        if sino:
            if i == 0:
                name = digit2name.get(digit, "")
            elif i == 1:
                name = digit2name.get(digit, "") + "십"
                name = name.replace("일십", "십")
        else:
            if i == 0:
                name = digit2mod.get(digit, "")
            elif i == 1:
                name = digit2dec.get(digit, "")
        if digit == "0":
            if i % 4 == 0:
                last_three = spelledout[-min(3, len(spelledout)) :]
                if "".join(last_three) == "":
                    spelledout.append("")
                    continue
            else:
                spelledout.append("")
                continue
        if i == 2:
            name = digit2name.get(digit, "") + "백"
            name = name.replace("일백", "백")
        elif i == 3:
            name = digit2name.get(digit, "") + "천"
            name = name.replace("일천", "천")
        elif i == 4:
            name = digit2name.get(digit, "") + "만"
            name = name.replace("일만", "만")
        elif i == 5:
            name = digit2name.get(digit, "") + "십"
            name = name.replace("일십", "십")
        elif i == 6:
            name = digit2name.get(digit, "") + "백"
            name = name.replace("일백", "백")
        elif i == 7:
            name = digit2name.get(digit, "") + "천"
            name = name.replace("일천", "천")
        elif i == 8:
            name = digit2name.get(digit, "") + "억"
        elif i == 9:
            name = digit2name.get(digit, "") + "십"
        elif i == 10:
            name = digit2name.get(digit, "") + "백"
        elif i == 11:
            name = digit2name.get(digit, "") + "천"
        elif i == 12:
            name = digit2name.get(digit, "") + "조"
        elif i == 13:
            name = digit2name.get(digit, "") + "십"
        elif i == 14:
            name = digit2name.get(digit, "") + "백"
        elif i == 15:
            name = digit2name.get(digit, "") + "천"
        spelledout.append(name)
    return "".join(elem for elem in spelledout)