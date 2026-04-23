def main():
    if len(sys.argv) == 1:
        print("Not enough arguments: directory containing OpenSSL",
              "sources must be supplied")
        sys.exit(1)

    if len(sys.argv) == 3 and sys.argv[2] not in ('x86', 'amd64'):
        print("Second argument must be x86 or amd64")
        sys.exit(1)

    if len(sys.argv) > 3:
        print("Too many arguments supplied, all we need is the directory",
              "containing OpenSSL sources and optionally the architecture")
        sys.exit(1)

    ssl_dir = sys.argv[1]
    arch = sys.argv[2] if len(sys.argv) >= 3 else None

    if not os.path.isdir(ssl_dir):
        print(ssl_dir, "is not an existing directory!")
        sys.exit(1)

    # perl should be on the path, but we also look in "\perl" and "c:\\perl"
    # as "well known" locations
    perls = find_all_on_path("perl.exe", [r"\perl\bin",
                                          r"C:\perl\bin",
                                          r"\perl64\bin",
                                          r"C:\perl64\bin",
                                         ])
    perl = find_working_perl(perls)
    if perl:
        print("Found a working perl at '%s'" % (perl,))
    else:
        sys.exit(1)
    if not find_all_on_path('nmake.exe'):
        print('Could not find nmake.exe, try running env.bat')
        sys.exit(1)
    if not find_all_on_path('nasm.exe'):
        print('Could not find nasm.exe, please add to PATH')
        sys.exit(1)
    sys.stdout.flush()

    # Put our working Perl at the front of our path
    os.environ["PATH"] = os.path.dirname(perl) + \
                                os.pathsep + \
                                os.environ["PATH"]

    old_cwd = os.getcwd()
    try:
        os.chdir(ssl_dir)
        if arch:
            prep(arch)
        else:
            for arch in ['amd64', 'x86']:
                prep(arch)
    finally:
        os.chdir(old_cwd)