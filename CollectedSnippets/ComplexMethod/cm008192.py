def convert(e):
            t = ''
            n = 0
            i = [0, 0, 0]
            a = [0, 0, 0, 0]
            s = len(e)
            c = 0
            for _ in range(s, 0, -1):
                if n <= 3:
                    i[n] = e[c]
                n += 1
                c += 1
                if 3 == n:
                    a[0] = (252 & i[0]) >> 2
                    a[1] = ((3 & i[0]) << 4) + ((240 & i[1]) >> 4)
                    a[2] = ((15 & i[1]) << 2) + ((192 & i[2]) >> 6)
                    a[3] = (63 & i[2])
                    for v in range(4):
                        t += r[a[v]]
                    n = 0
            if n:
                for o in range(n, 3):
                    i[o] = 0

                for o in range(n + 1):
                    a[0] = (252 & i[0]) >> 2
                    a[1] = ((3 & i[0]) << 4) + ((240 & i[1]) >> 4)
                    a[2] = ((15 & i[1]) << 2) + ((192 & i[2]) >> 6)
                    a[3] = (63 & i[2])
                    t += r[a[o]]
                n += 1
                while n < 3:
                    t += ''
                    n += 1
            return t