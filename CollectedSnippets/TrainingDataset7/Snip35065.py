def __init__(self, *args, **kwargs):
        if parallel := kwargs.get("parallel"):
            sys.stderr.write(f"parallel={parallel}")
        if durations := kwargs.get("durations"):
            sys.stderr.write(f"durations={durations}")