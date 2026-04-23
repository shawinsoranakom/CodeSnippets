def fix_corner(top_line, bot_line, start_box, end_box):
    assert isinstance(top_line, list)
    assert all(isinstance(point, list) for point in top_line)
    assert isinstance(bot_line, list)
    assert all(isinstance(point, list) for point in bot_line)
    assert start_box.shape == end_box.shape == (4, 2)

    contour = np.array(top_line + bot_line[::-1])
    start_left_mid = (start_box[0] + start_box[3]) / 2
    start_right_mid = (start_box[1] + start_box[2]) / 2
    end_left_mid = (end_box[0] + end_box[3]) / 2
    end_right_mid = (end_box[1] + end_box[2]) / 2
    if not in_contour(contour, start_left_mid):
        top_line.insert(0, start_box[0].tolist())
        bot_line.insert(0, start_box[3].tolist())
    elif not in_contour(contour, start_right_mid):
        top_line.insert(0, start_box[1].tolist())
        bot_line.insert(0, start_box[2].tolist())
    if not in_contour(contour, end_left_mid):
        top_line.append(end_box[0].tolist())
        bot_line.append(end_box[3].tolist())
    elif not in_contour(contour, end_right_mid):
        top_line.append(end_box[1].tolist())
        bot_line.append(end_box[2].tolist())
    return top_line, bot_line