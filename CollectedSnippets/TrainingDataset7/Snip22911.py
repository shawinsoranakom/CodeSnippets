def bad_names(value):
            if value == "bad value":
                raise ValidationError("bad value not allowed")