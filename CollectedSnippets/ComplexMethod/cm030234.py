def _format_size(size, sign):
    for unit in ('B', 'KiB', 'MiB', 'GiB', 'TiB'):
        if abs(size) < 100 and unit != 'B':
            # 3 digits (xx.x UNIT)
            if sign:
                return "%+.1f %s" % (size, unit)
            else:
                return "%.1f %s" % (size, unit)
        if abs(size) < 10 * 1024 or unit == 'TiB':
            # 4 or 5 digits (xxxx UNIT)
            if sign:
                return "%+.0f %s" % (size, unit)
            else:
                return "%.0f %s" % (size, unit)
        size /= 1024