def fix_kv(m):
        v = m.group(0)
        if v in ('true', 'false', 'null'):
            return v
        elif v in ('undefined', 'void 0'):
            return 'null'
        elif v.startswith('/*') or v.startswith('//') or v == ',':
            return ''

        if v[0] in STRING_QUOTES:
            v = re.sub(r'(?s)\${([^}]+)}', template_substitute, v[1:-1]) if v[0] == '`' else v[1:-1]
            escaped = re.sub(r'(?s)(")|\\(.)', process_escape, v)
            return '"{0}"'.format(escaped)

        inv = IDENTITY
        im = re.split(r'^!+', v)
        if len(im) > 1 and not im[-1].endswith(':'):
            if (len(v) - len(im[1])) % 2 == 1:
                inv = lambda x: 'true' if x == 0 else 'false'
            else:
                inv = lambda x: 'false' if x == 0 else 'true'
        if not any(x for x in im):
            return
        v = im[-1]

        for regex, base in INTEGER_TABLE:
            im = re.match(regex, v)
            if im:
                i = int(im.group(1), base)
                return ('"%s":' if v.endswith(':') else '%s') % inv(i)

        if v in vars:
            try:
                if not strict:
                    json.loads(vars[v])
            except JSONDecodeError:
                return inv(json.dumps(vars[v]))
            else:
                return inv(vars[v])

        if not strict:
            v = try_call(inv, args=(v,), default=v)
            if v in ('true', 'false'):
                return v
            return '"{0}"'.format(v)

        raise ValueError('Unknown value: ' + v)