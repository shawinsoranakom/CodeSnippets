def invoke(self, args, from_tty):
        import re

        start = None
        end = None

        m = re.match(r'\s*(\d+)\s*', args)
        if m:
            start = int(m.group(0))
            end = start + 10

        m = re.match(r'\s*(\d+)\s*,\s*(\d+)\s*', args)
        if m:
            start, end = map(int, m.groups())

        # py-list requires an actual PyEval_EvalFrameEx frame:
        frame = Frame.get_selected_bytecode_frame()
        if not frame:
            print('Unable to locate gdb frame for python bytecode interpreter')
            return

        pyop = frame.get_pyop()
        if not pyop or pyop.is_optimized_out():
            print(UNABLE_READ_INFO_PYTHON_FRAME)
            return

        filename = pyop.filename()
        lineno = pyop.current_line_num()
        if lineno is None:
            print('Unable to read python frame line number')
            return

        if start is None:
            start = lineno - 5
            end = lineno + 5

        if start<1:
            start = 1

        try:
            f = open(os.fsencode(filename), 'r', encoding="utf-8")
        except IOError as err:
            sys.stdout.write('Unable to open %s: %s\n'
                             % (filename, err))
            return
        with f:
            all_lines = f.readlines()
            # start and end are 1-based, all_lines is 0-based;
            # so [start-1:end] as a python slice gives us [start, end] as a
            # closed interval
            for i, line in enumerate(all_lines[start-1:end]):
                linestr = str(i+start)
                # Highlight current line:
                if i + start == lineno:
                    linestr = '>' + linestr
                sys.stdout.write('%4s    %s' % (linestr, line))