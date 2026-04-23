def generate_runtime_init(identifiers, strings):
    nsmallnegints, nsmallposints = consts_getter.get_nsmallnegints_and_nsmallposints()

    # Then target the runtime initializer.
    filename = os.path.join(INTERNAL, 'pycore_runtime_init_generated.h')

    # Read the non-generated part of the file.
    with open(filename) as infile:
        orig = infile.read()
    lines = iter(orig.rstrip().splitlines())
    before = '\n'.join(iter_to_marker(lines, START))
    for _ in iter_to_marker(lines, END):
        pass
    after = '\n'.join(lines)

    # Generate the file.
    with open_for_changes(filename, orig) as outfile:
        immortal_objects = []
        printer = Printer(outfile)
        printer.write(before)
        printer.write(START)
        with printer.block('#define _Py_small_ints_INIT', continuation=True):
            for i in range(-nsmallnegints, nsmallposints):
                printer.write(f'_PyLong_DIGIT_INIT({i}),')
                immortal_objects.append(f'(PyObject *)&_Py_SINGLETON(small_ints)[_PY_NSMALLNEGINTS + {i}]')
        printer.write('')
        with printer.block('#define _Py_bytes_characters_INIT', continuation=True):
            for i in range(256):
                printer.write(f'_PyBytes_CHAR_INIT({i}),')
                immortal_objects.append(f'(PyObject *)&_Py_SINGLETON(bytes_characters)[{i}]')
        printer.write('')
        with printer.block('#define _Py_str_literals_INIT', continuation=True):
            for literal, name in sorted(strings.items(), key=lambda x: x[1]):
                printer.write(f'INIT_STR({name}, "{literal}"),')
                immortal_objects.append(f'(PyObject *)&_Py_STR({name})')
        printer.write('')
        with printer.block('#define _Py_str_identifiers_INIT', continuation=True):
            for name in sorted(identifiers):
                assert name.isidentifier(), name
                printer.write(f'INIT_ID({name}),')
                immortal_objects.append(f'(PyObject *)&_Py_ID({name})')
        printer.write('')
        with printer.block('#define _Py_str_ascii_INIT', continuation=True):
            for i in range(128):
                printer.write(f'_PyASCIIObject_INIT("\\x{i:02x}"),')
                immortal_objects.append(f'(PyObject *)&_Py_SINGLETON(strings).ascii[{i}]')
        printer.write('')
        with printer.block('#define _Py_str_latin1_INIT', continuation=True):
            for i in range(128, 256):
                utf8 = ['"']
                for c in chr(i).encode('utf-8'):
                    utf8.append(f"\\x{c:02x}")
                utf8.append('"')
                printer.write(f'_PyUnicode_LATIN1_INIT("\\x{i:02x}", {"".join(utf8)}),')
                immortal_objects.append(f'(PyObject *)&_Py_SINGLETON(strings).latin1[{i} - 128]')
        printer.write(END)
        printer.write(after)
        return immortal_objects