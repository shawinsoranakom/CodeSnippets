def create_package(test_dir, source):
    ofi = None
    try:
        for line in source.splitlines():
            if type(line) != bytes:
                line = line.encode('utf-8')
            if line.startswith(b' ') or line.startswith(b'\t'):
                ofi.write(line.strip() + b'\n')
            else:
                if ofi:
                    ofi.close()
                if type(line) == bytes:
                    line = line.decode('utf-8')
                ofi = open_file(os.path.join(test_dir, line.strip()))
    finally:
        if ofi:
            ofi.close()