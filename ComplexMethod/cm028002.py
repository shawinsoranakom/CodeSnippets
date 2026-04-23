def choose_bug_description() -> str:
    """Let the user choose one of the examples or paste their own bug."""
    print("Choose an example or paste your own bug description:\n")
    print("  [1] Example 1 — retrieval hallucination (P01 style)")
    print("  [2] Example 2 — startup ordering / dependency not ready (P10 style)")
    print("  [3] Example 3 — config or secrets drift (P11 style)")
    print("  [p] Paste my own RAG / LLM bug\n")

    choice = input("Your choice: ").strip().lower()
    print()

    if choice == "1":
        bug = EXAMPLE_1
        print("You selected Example 1. Full bug description:\n")
        print(bug)
        print()
        return bug

    if choice == "2":
        bug = EXAMPLE_2
        print("You selected Example 2. Full bug description:\n")
        print(bug)
        print()
        return bug

    if choice == "3":
        bug = EXAMPLE_3
        print("You selected Example 3. Full bug description:\n")
        print(bug)
        print()
        return bug

    print("Paste your bug description. End with an empty line.")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line.strip():
            break
        lines.append(line)

    user_bug = "\n".join(lines).strip()
    if not user_bug:
        print("No bug description detected, aborting this round.\n")
        return ""

    print("\nYou pasted the following bug description:\n")
    print(user_bug)
    print()
    return user_bug