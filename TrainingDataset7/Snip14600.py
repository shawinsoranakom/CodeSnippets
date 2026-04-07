def calculate_truncate_chars_length(length, replacement):
    truncate_len = length
    for char in add_truncation_text("", replacement):
        if not unicodedata.combining(char):
            truncate_len -= 1
            if truncate_len == 0:
                break
    return truncate_len