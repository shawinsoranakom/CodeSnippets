def get_field_size(name):
    """Extract the size number from a "varchar(11)" type name"""
    m = field_size_re.search(name)
    return int(m[1]) if m else None