def get_field_value(field, params):
            value = field.function(params) if field.function else params.get(field.label)
            if value is None:
                return None

            if field.api in request.__fields__:
                target_type = request.__fields__[field.api].type_
            else:
                target_type = type(field.component.value)

            if target_type == type(None):
                return None

            if isinstance(value, dict) and value.get('__type__') == 'generic_update':  # this is a gradio.update rather than a value
                value = value.get('value')

            if value is not None and not isinstance(value, target_type):
                value = target_type(value)

            return value