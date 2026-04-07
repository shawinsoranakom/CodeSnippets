def time_format(value, format_string):
    "Convenience function"
    tf = TimeFormat(value)
    return tf.format(format_string)