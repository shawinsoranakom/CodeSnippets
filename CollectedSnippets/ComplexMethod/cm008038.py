def _traverse_infodict(fields):
            fields = [f for x in re.split(r'\.({.+?})\.?', fields)
                      for f in ([x] if x.startswith('{') else x.split('.'))]
            for i in (0, -1):
                if fields and not fields[i]:
                    fields.pop(i)

            for i, f in enumerate(fields):
                if not f.startswith('{'):
                    fields[i] = _from_user_input(f)
                    continue
                assert f.endswith('}'), f'No closing brace for {f} in {fields}'
                fields[i] = {k: list(map(_from_user_input, k.split('.'))) for k in f[1:-1].split(',')}

            return traverse_obj(info_dict, fields, traverse_string=True)