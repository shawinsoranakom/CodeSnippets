def convert_message_field_to_infinity(field_name: str, table_fields: list[str]=None):
        match field_name:
            case "message_type":
                return "message_type_kwd"
            case "status":
                return "status_int"
            case "content_embed":
                if not table_fields:
                    raise Exception("Can't convert 'content_embed' to vector field name with empty table fields.")
                vector_field = [tf for tf in table_fields if re.match(r"q_\d+_vec", tf)]
                if not vector_field:
                    raise Exception("Can't convert 'content_embed' to vector field name. No match field name found.")
                return vector_field[0]
            case _:
                return field_name