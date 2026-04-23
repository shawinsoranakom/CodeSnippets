def format(value, format_string):
    "Convenience function"
    df = DateFormat(value)
    return df.format(format_string)