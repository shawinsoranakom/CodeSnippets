def main(argv, output_stream=None) -> int | None:
    if len(argv) != 2:
        # Don't spam stderr if not using stdout.
        if output_stream is not None:
            raise Exception("Pass argv of length 2.")  # noqa: TRY002
        sys.stderr.write("usage: show_pickle PICKLE_FILE\n")
        sys.stderr.write("  PICKLE_FILE can be any of:\n")
        sys.stderr.write("    path to a pickle file\n")
        sys.stderr.write("    file.zip@member.pkl\n")
        sys.stderr.write("    file.zip@*/pattern.*\n")
        sys.stderr.write("      (shell glob pattern for members)\n")
        sys.stderr.write("      (only first match will be shown)\n")
        return 2

    fname = argv[1]
    handle: IO[bytes]
    if "@" not in fname:
        with open(fname, "rb") as handle:
            DumpUnpickler.dump(handle, output_stream)
    else:
        zfname, mname = fname.split("@", 1)
        with zipfile.ZipFile(zfname) as zf:
            if "*" not in mname:
                with zf.open(mname) as handle:
                    DumpUnpickler.dump(handle, output_stream)
            else:
                found = False
                for info in zf.infolist():
                    if fnmatch.fnmatch(info.filename, mname):
                        with zf.open(info) as handle:
                            DumpUnpickler.dump(handle, output_stream)
                        found = True
                        break
                if not found:
                    raise Exception(f"Could not find member matching {mname} in {zfname}")