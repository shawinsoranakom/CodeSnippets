def combinefile(f):
    fi = iter(f)

    for line in read(fi, re.compile(r'^Remaining objects:$'), False):
        pass

    crack = re.compile(r'([a-zA-Z\d]+) \[(\d+)\] (.*)')
    addr2rc = {}
    addr2guts = {}
    before = 0
    for line in read(fi, re.compile(r'^Remaining object addresses:$'), False):
        m = crack.match(line)
        if m:
            addr, addr2rc[addr], addr2guts[addr] = m.groups()
            before += 1
        else:
            print('??? skipped:', line)

    after = 0
    for line in read(fi, crack, True):
        after += 1
        m = crack.match(line)
        assert m
        addr, rc, guts = m.groups() # guts is type name here
        if addr not in addr2rc:
            print('??? new object created while tearing down:', line.rstrip())
            continue
        print(addr, end=' ')
        if rc == addr2rc[addr]:
            print('[%s]' % rc, end=' ')
        else:
            print('[%s->%s]' % (addr2rc[addr], rc), end=' ')
        print(guts, addr2guts[addr])

    print("%d objects before, %d after" % (before, after))