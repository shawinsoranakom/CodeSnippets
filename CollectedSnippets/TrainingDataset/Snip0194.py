def format_ruleset(ruleset: int) -> list[int]:
   
    return [int(c) for c in f"{ruleset:08}"[:8]]
