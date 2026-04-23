def simplify_kmap(kmap: list[list[int]]) -> str:
    
    simplified_f = []
    for a, row in enumerate(kmap):
        for b, item in enumerate(row):
            if item:
                term = ("A" if a else "A'") + ("B" if b else "B'")
                simplified_f.append(term)
    return " + ".join(simplified_f)
