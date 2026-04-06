def _get_output_lines(output):
    lines = output.split('\n')
    screen = pyte.Screen(get_terminal_size().columns, len(lines))
    stream = pyte.Stream(screen)
    stream.feed('\n'.join(lines))
    return screen.display