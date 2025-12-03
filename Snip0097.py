def mmain() -> None:
    scores = [90, 23, 6, 33, 21, 65, 123, 34423]
    height = math.log(len(scores), 2)

    print("Optimal value : ", end="")
    print(minimax(0, 0, True, scores, height))
