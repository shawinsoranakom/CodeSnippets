def run(canvas: list[list[bool]]) -> list[list[bool]]:

    current_canvas = np.array(canvas)
    next_gen_canvas = np.array(create_canvas(current_canvas.shape[0]))
    for r, row in enumerate(current_canvas):
        for c, pt in enumerate(row):
            next_gen_canvas[r][c] = __judge_point(
                pt, current_canvas[r - 1 : r + 2, c - 1 : c + 2]
            )

    return next_gen_canvas.tolist()
