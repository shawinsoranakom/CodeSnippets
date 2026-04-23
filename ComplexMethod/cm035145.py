def extract_math_from_paragraph(para_element) -> list:
    """Extract LaTeX strings from math elements in a DrawingML paragraph XML element.

    Handles three nesting patterns:
    1. a14:m → m:oMath (or m:oMathPara → m:oMath)
    2. Direct m:oMathPara → m:oMath (not wrapped in a14:m)
    3. Direct m:oMath (not inside a14:m or m:oMathPara)
    """
    results = []
    # a14:m wraps m:oMathPara or m:oMath
    for a14m in para_element.findall(f".//{_A14}m"):
        found_omath = False
        for omath in a14m.findall(f".//{_M}oMath"):
            latex = convert_omath(omath)
            if latex:
                results.append(latex)
                found_omath = True
        # No oMath inside this a14:m? Try the a14:m element itself
        if not found_omath:
            latex = convert_omath(a14m)
            if latex:
                results.append(latex)
    # Direct m:oMathPara / m:oMath not wrapped in a14:m
    for omath_para in para_element.findall(f".//{_M}oMathPara"):
        parent = omath_para.getparent()
        if parent is not None and parent.tag == f"{_A14}m":
            continue  # already handled above (oMathPara is inside a14:m)
        for omath in omath_para.findall(f"{_M}oMath"):
            latex = convert_omath(omath)
            if latex:
                results.append(latex)
    for omath in para_element.findall(f".//{_M}oMath"):
        parent = omath.getparent()
        if parent is not None and parent.tag in (f"{_A14}m", f"{_M}oMathPara"):
            continue  # already handled
        latex = convert_omath(omath)
        if latex:
            results.append(latex)
    return results