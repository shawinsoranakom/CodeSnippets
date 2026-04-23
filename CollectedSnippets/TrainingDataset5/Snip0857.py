def adjm():
    n = int(input().strip())
    a = []
    for _ in range(n):
        a.append(tuple(map(int, input().strip().split())))
    return a, n
