def check_inst_exn_tab_entries_valid(instructions: list[Instruction]) -> None:
    """
    Checks that exn_tab_entries of instructions are valid.
    An entry's start, end, and target must be in instructions.
    Instructions with an exn_tab_entry are located within
    the entry's start and end instructions.
    Instructions do not share exn_tab_entries.

    Implicitly checks for no duplicate instructions.
    """
    indexof = get_indexof(instructions)
    exn_tab_entry_set = set()
    for i, inst in enumerate(instructions):
        if inst.exn_tab_entry:
            assert sys.version_info >= (3, 11)
            assert id(inst.exn_tab_entry) not in exn_tab_entry_set
            exn_tab_entry_set.add(id(inst.exn_tab_entry))
            entry = inst.exn_tab_entry
            assert entry.start in indexof
            assert entry.end in indexof
            assert entry.target in indexof
            assert indexof[entry.start] <= i <= indexof[entry.end]