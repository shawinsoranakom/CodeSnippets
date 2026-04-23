def selection(chart: list[list[int]], prime_implicants: list[str]) -> list[str]:
  
    temp = []
    select = [0] * len(chart)
    for i in range(len(chart[0])):
        count = sum(row[i] == 1 for row in chart)
        if count == 1:
            rem = max(j for j, row in enumerate(chart) if row[i] == 1)
            select[rem] = 1
    for i, item in enumerate(select):
        if item != 1:
            continue
        for j in range(len(chart[0])):
            if chart[i][j] != 1:
                continue
            for row in chart:
                row[j] = 0
        temp.append(prime_implicants[i])
    while True:
        counts = [chart[i].count(1) for i in range(len(chart))]
        max_n = max(counts)
        rem = counts.index(max_n)

        if max_n == 0:
            return temp

        temp.append(prime_implicants[rem])

        for j in range(len(chart[0])):
            if chart[rem][j] != 1:
                continue
            for i in range(len(chart)):
                chart[i][j] = 0
