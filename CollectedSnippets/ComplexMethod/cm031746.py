def makeconfig(infp, outfp, modules, with_ifdef=0):
    m1 = re.compile('-- ADDMODULE MARKER 1 --')
    m2 = re.compile('-- ADDMODULE MARKER 2 --')
    for line in infp:
        outfp.write(line)
        if m1 and m1.search(line):
            m1 = None
            for mod in modules:
                if mod in never:
                    continue
                if with_ifdef:
                    outfp.write("#ifndef PyInit_%s\n"%mod)
                outfp.write('extern PyObject* PyInit_%s(void);\n' % mod)
                if with_ifdef:
                    outfp.write("#endif\n")
        elif m2 and m2.search(line):
            m2 = None
            for mod in modules:
                if mod in never:
                    continue
                outfp.write('\t{"%s", PyInit_%s},\n' %
                            (mod, mod))
    if m1:
        sys.stderr.write('MARKER 1 never found\n')
    elif m2:
        sys.stderr.write('MARKER 2 never found\n')