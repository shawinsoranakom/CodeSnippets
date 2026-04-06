def _switch(ch, layout):
    if ch in layout:
        return target_layout[layout.index(ch)]
    return ch