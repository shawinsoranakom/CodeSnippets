def _eval_xml(self, node, env):
    if node.tag in ('field','value'):
        t = node.get('type','char')
        f_model = node.get('model')
        if f_search := node.get('search'):
            f_use = node.get("use",'id')
            f_name = node.get("name")
            context = _get_eval_context(self, env, f_model)
            q = safe_eval(f_search, context)
            ids = env[f_model].search(q).ids
            if f_use != 'id':
                ids = [x[f_use] for x in env[f_model].browse(ids).read([f_use])]
            _fields = env[f_model]._fields
            if (f_name in _fields) and _fields[f_name].type == 'many2many':
                return ids
            f_val = False
            if len(ids):
                f_val = ids[0]
                if isinstance(f_val, tuple):
                    f_val = f_val[0]
            return f_val
        if a_eval := node.get('eval'):
            context = _get_eval_context(self, env, f_model)
            try:
                return safe_eval(a_eval, context)
            except Exception:
                logging.getLogger('odoo.tools.convert.init').error(
                    'Could not eval(%s) for %s in %s', a_eval, node.get('name'), env.context)
                raise
        def _process(s):
            matches = re.finditer(br'[^%]%\((.*?)\)[ds]'.decode('utf-8'), s)
            done = set()
            for m in matches:
                found = m.group()[1:]
                if found in done:
                    continue
                done.add(found)
                rec_id = m[1]
                xid = self.make_xml_id(rec_id)
                if (record_id := self.idref.get(xid)) is None:
                    record_id = self.idref[xid] = self.id_get(xid)
                # So funny story: in Python 3, bytes(n: int) returns a
                # bytestring of n nuls. In Python 2 it obviously returns the
                # stringified number, which is what we're expecting here
                s = s.replace(found, str(record_id))
            s = s.replace('%%', '%') # Quite weird but it's for (somewhat) backward compatibility sake
            return s

        if t == 'xml':
            _fix_multiple_roots(node)
            return '<?xml version="1.0"?>\n'\
                +_process("".join(etree.tostring(n, encoding='unicode') for n in node))
        if t == 'html':
            return _process("".join(etree.tostring(n, method='html', encoding='unicode') for n in node))

        if node.get('file'):
            if t == 'base64':
                with file_open(node.get('file'), 'rb', env=env) as f:
                    return base64.b64encode(f.read())

            with file_open(node.get('file'), env=env) as f:
                data = f.read()
        else:
            data = node.text or ''

        match t:
            case 'file':
                path = data.strip()
                try:
                    file_path(os.path.join(self.module, path))
                except FileNotFoundError:
                    raise FileNotFoundError(
                        f"No such file or directory: {path!r} in {self.module}"
                    ) from None
                return '%s,%s' % (self.module, path)
            case 'char':
                return data
            case 'int':
                d = data.strip()
                if d == 'None':
                    return None
                return int(d)
            case 'float':
                return float(data.strip())
            case 'list':
                return [_eval_xml(self, n, env) for n in node.iterchildren('value')]
            case 'tuple':
                return tuple(_eval_xml(self, n, env) for n in node.iterchildren('value'))
            case 'base64':
                raise ValueError("base64 type is only compatible with file data")
            case t:
                raise ValueError(f"Unknown type {t!r}")

    elif node.tag == "function":
        from odoo.models import BaseModel  # noqa: PLC0415
        model_str = node.get('model')
        model = env[model_str]
        method_name = node.get('name')
        # determine arguments
        args = []
        kwargs = {}

        if a_eval := node.get('eval'):
            context = _get_eval_context(self, env, model_str)
            args = list(safe_eval(a_eval, context))
        for child in node:
            if child.tag == 'value' and child.get('name'):
                kwargs[child.get('name')] = _eval_xml(self, child, env)
            else:
                args.append(_eval_xml(self, child, env))
        # merge current context with context in kwargs
        if 'context' in kwargs:
            model = model.with_context(**kwargs.pop('context'))
        method = getattr(model, method_name)
        is_model_method = getattr(method, '_api_model', False)
        if is_model_method:
            pass  # already bound to an empty recordset
        else:
            record_ids, *args = args
            model = model.browse(record_ids)
            method = getattr(model, method_name)
        # invoke method
        result = method(*args, **kwargs)
        if isinstance(result, BaseModel):
            result = result.ids
        return result
    elif node.tag == "test":
        return node.text