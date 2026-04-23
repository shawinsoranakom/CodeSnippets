def is_equation(txt):
    """
    判定是否为公式 | 测试1 写出洛伦兹定律，使用tex格式公式 测试2 给出柯西不等式，使用latex格式 测试3 写出麦克斯韦方程组
    """
    if "```" in txt and "```reference" not in txt:
        return False
    if "$" not in txt and "\\[" not in txt:
        return False

    matches = []
    for pattern, property in mathpatterns.items():
        flags = re.ASCII | re.DOTALL if property["allow_multi_lines"] else re.ASCII
        matches.extend(re.findall(pattern, txt, flags))
    if len(matches) == 0:
        return False
    contain_any_eq = False
    illegal_pattern = re.compile(r"[^\x00-\x7F]|echo")
    for match in matches:
        if len(match) != 3:
            return False
        eq_canidate = match[1]
        if illegal_pattern.search(eq_canidate):
            return False
        else:
            contain_any_eq = True
    return contain_any_eq