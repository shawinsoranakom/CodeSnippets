def dis(pickle, out=None, memo=None, indentlevel=4, annotate=0):
    """Produce a symbolic disassembly of a pickle.

    'pickle' is a file-like object, or string, containing a (at least one)
    pickle.  The pickle is disassembled from the current position, through
    the first STOP opcode encountered.

    Optional arg 'out' is a file-like object to which the disassembly is
    printed.  It defaults to sys.stdout.

    Optional arg 'memo' is a Python dict, used as the pickle's memo.  It
    may be mutated by dis(), if the pickle contains PUT or BINPUT opcodes.
    Passing the same memo object to another dis() call then allows disassembly
    to proceed across multiple pickles that were all created by the same
    pickler with the same memo.  Ordinarily you don't need to worry about this.

    Optional arg 'indentlevel' is the number of blanks by which to indent
    a new MARK level.  It defaults to 4.

    Optional arg 'annotate' if nonzero instructs dis() to add short
    description of the opcode on each line of disassembled output.
    The value given to 'annotate' must be an integer and is used as a
    hint for the column where annotation should start.  The default
    value is 0, meaning no annotations.

    In addition to printing the disassembly, some sanity checks are made:

    + All embedded opcode arguments "make sense".

    + Explicit and implicit pop operations have enough items on the stack.

    + When an opcode implicitly refers to a markobject, a markobject is
      actually on the stack.

    + A memo entry isn't referenced before it's defined.

    + The markobject isn't stored in the memo.
    """

    # Most of the hair here is for sanity checks, but most of it is needed
    # anyway to detect when a protocol 0 POP takes a MARK off the stack
    # (which in turn is needed to indent MARK blocks correctly).

    stack = []          # crude emulation of unpickler stack
    if memo is None:
        memo = {}       # crude emulation of unpickler memo
    maxproto = -1       # max protocol number seen
    markstack = []      # bytecode positions of MARK opcodes
    indentchunk = ' ' * indentlevel
    errormsg = None
    annocol = annotate  # column hint for annotations
    for opcode, arg, pos in genops(pickle):
        if pos is not None:
            print("%5d:" % pos, end=' ', file=out)

        line = "%-4s %s%s" % (repr(opcode.code)[1:-1],
                              indentchunk * len(markstack),
                              opcode.name)

        maxproto = max(maxproto, opcode.proto)
        before = opcode.stack_before    # don't mutate
        after = opcode.stack_after      # don't mutate
        numtopop = len(before)

        # See whether a MARK should be popped.
        markmsg = None
        if markobject in before or (opcode.name == "POP" and
                                    stack and
                                    stack[-1] is markobject):
            assert markobject not in after
            if __debug__:
                if markobject in before:
                    assert before[-1] is stackslice
            if markstack:
                markpos = markstack.pop()
                if markpos is None:
                    markmsg = "(MARK at unknown opcode offset)"
                else:
                    markmsg = "(MARK at %d)" % markpos
                # Pop everything at and after the topmost markobject.
                while stack[-1] is not markobject:
                    stack.pop()
                stack.pop()
                # Stop later code from popping too much.
                try:
                    numtopop = before.index(markobject)
                except ValueError:
                    assert opcode.name == "POP"
                    numtopop = 0
            else:
                errormsg = "no MARK exists on stack"

        # Check for correct memo usage.
        if opcode.name in ("PUT", "BINPUT", "LONG_BINPUT", "MEMOIZE"):
            if opcode.name == "MEMOIZE":
                memo_idx = len(memo)
                markmsg = "(as %d)" % memo_idx
            else:
                assert arg is not None
                memo_idx = arg
            if not stack:
                errormsg = "stack is empty -- can't store into memo"
            elif stack[-1] is markobject:
                errormsg = "can't store markobject in the memo"
            else:
                memo[memo_idx] = stack[-1]
        elif opcode.name in ("GET", "BINGET", "LONG_BINGET"):
            if arg in memo:
                assert len(after) == 1
                after = [memo[arg]]     # for better stack emulation
            else:
                errormsg = "memo key %r has never been stored into" % arg

        if arg is not None or markmsg:
            # make a mild effort to align arguments
            line += ' ' * (10 - len(opcode.name))
            if arg is not None:
                if opcode.name in ("STRING", "BINSTRING", "SHORT_BINSTRING"):
                    line += ' ' + ascii(arg)
                else:
                    line += ' ' + repr(arg)
            if markmsg:
                line += ' ' + markmsg
        if annotate:
            line += ' ' * (annocol - len(line))
            # make a mild effort to align annotations
            annocol = len(line)
            if annocol > 50:
                annocol = annotate
            line += ' ' + opcode.doc.split('\n', 1)[0]
        print(line, file=out)

        if errormsg:
            # Note that we delayed complaining until the offending opcode
            # was printed.
            raise ValueError(errormsg)

        # Emulate the stack effects.
        if len(stack) < numtopop:
            raise ValueError("tries to pop %d items from stack with "
                             "only %d items" % (numtopop, len(stack)))
        if numtopop:
            del stack[-numtopop:]
        if markobject in after:
            assert markobject not in before
            markstack.append(pos)

        stack.extend(after)

    print("highest protocol among opcodes =", maxproto, file=out)
    if stack:
        raise ValueError("stack not empty after STOP: %r" % stack)