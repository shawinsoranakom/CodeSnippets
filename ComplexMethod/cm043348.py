def parse_key_values(ctx, param, value) -> Dict[str, Any]:
    if not value:
        return {}
    result = {}
    pairs = value.split(',')
    for pair in pairs:
        try:
            k, v = pair.split('=', 1)
            # Handle common value types 
            if v.lower() == 'true': v = True
            elif v.lower() == 'false': v = False
            elif v.isdigit(): v = int(v)
            elif v.replace('.','',1).isdigit(): v = float(v)
            elif v.startswith('[') and v.endswith(']'):
                v = [x.strip() for x in v[1:-1].split(',') if x.strip()]
            elif v.startswith('{') and v.endswith('}'):
                try:
                    v = json.loads(v)
                except json.JSONDecodeError:
                    raise click.BadParameter(f'Invalid JSON object: {v}')
            result[k.strip()] = v
        except ValueError:
            raise click.BadParameter(f'Invalid key=value pair: {pair}')
    return result