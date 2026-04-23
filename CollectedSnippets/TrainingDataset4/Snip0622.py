def calculate_span(price: list[int]) -> list[int]:
    n = len(price)
    s = [0] * n
    st = []
    st.append(0)

    s[0] = 1
    for i in range(1, n):
        while len(st) > 0 and price[st[-1]] <= price[i]:
            st.pop()
        s[i] = i + 1 if len(st) <= 0 else (i - st[-1])
        st.append(i)

    return s
