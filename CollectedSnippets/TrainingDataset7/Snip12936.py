def __init__(self, media_type_raw_line):
        full_type, self.params = parse_header_parameters(
            media_type_raw_line if media_type_raw_line else ""
        )
        self.main_type, _, self.sub_type = full_type.partition("/")