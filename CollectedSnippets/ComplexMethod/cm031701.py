def determine_num_threads_and_affinity():
    if sys.platform != "linux":
        return [None] * os.cpu_count()

    # Try to use `lscpu -p` on Linux
    import subprocess
    try:
        output = subprocess.check_output(["lscpu", "-p=cpu,node,core,MAXMHZ"],
                                         text=True, env={"LC_NUMERIC": "C"})
    except (FileNotFoundError, subprocess.CalledProcessError):
        return [None] * os.cpu_count()

    table = []
    for line in output.splitlines():
        if line.startswith("#"):
            continue
        cpu, node, core, maxhz = line.split(",")
        if maxhz == "":
            maxhz = "0"
        table.append((int(cpu), int(node), int(core), float(maxhz)))

    cpus = []
    cores = set()
    max_mhz_all = max(row[3] for row in table)
    for cpu, node, core, maxmhz in table:
        # Choose only CPUs on the same node, unique cores, and try to avoid
        # "efficiency" cores.
        if node == 0 and core not in cores and maxmhz == max_mhz_all:
            cpus.append(cpu)
            cores.add(core)
    return cpus