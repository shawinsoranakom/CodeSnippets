def _ensure_type(value: object, value_type: str | None, origin: str | None = None) -> t.Any:
    """Internal implementation for `ensure_type`, call that function instead."""
    original_value = value
    basedir = origin if origin and os.path.isabs(origin) and os.path.exists(to_bytes(origin)) else None

    if value_type:
        value_type = value_type.lower()

    match value_type:
        case 'boolean' | 'bool':
            return boolean(value, strict=False)

        case 'integer' | 'int':
            if isinstance(value, int):  # handle both int and bool (which is an int)
                return int(value)

            if isinstance(value, (float, str)):
                try:
                    # use Decimal for all other source type conversions; non-zero mantissa is a failure
                    if (decimal_value := decimal.Decimal(value)) == (int_part := int(decimal_value)):
                        return int_part
                except (decimal.DecimalException, ValueError):
                    pass

        case 'float':
            if isinstance(value, float):
                return value

            if isinstance(value, (int, str)):
                try:
                    return float(value)
                except ValueError:
                    pass

        case 'list':
            if isinstance(value, list):
                return value

            if isinstance(value, str):
                return [unquote(x.strip()) for x in value.split(',')]

            if isinstance(value, Sequence) and not isinstance(value, bytes):
                return list(value)

        case 'none':
            if value == "None":
                return None

        case 'path':
            if isinstance(value, str):
                return resolve_path(value, basedir=basedir)

        case 'temppath' | 'tmppath' | 'tmp':
            if isinstance(value, str):
                value = resolve_path(value, basedir=basedir)

                if not os.path.exists(value):
                    makedirs_safe(value, 0o700)

                prefix = 'ansible-local-%s' % os.getpid()
                value = tempfile.mkdtemp(prefix=prefix, dir=value)
                atexit.register(cleanup_tmp_file, value, warn=True)

                return value

        case 'pathspec':
            if isinstance(value, str):
                value = value.split(os.pathsep)

            if isinstance(value, Sequence) and not isinstance(value, bytes) and all(isinstance(x, str) for x in value):
                return [resolve_path(x, basedir=basedir) for x in value]

        case 'pathlist':
            if isinstance(value, str):
                value = [x.strip() for x in value.split(',')]

            if isinstance(value, Sequence) and not isinstance(value, bytes) and all(isinstance(x, str) for x in value):
                return [resolve_path(x, basedir=basedir) for x in value]

        case 'dictionary' | 'dict':
            if isinstance(value, dict):
                return value

            if isinstance(value, Mapping):
                return dict(value)

        case 'string' | 'str':
            if isinstance(value, str):
                return value

            if isinstance(value, (bool, int, float, complex)):
                return str(value)

            if isinstance(value, _EncryptedStringProtocol):
                return value._decrypt()

        case _:
            # FIXME: define and document a pass-through value_type (None, 'raw', 'object', '', ...) and then deprecate acceptance of unknown types
            return value  # return non-str values of unknown value_type as-is

    raise ValueError(f'Invalid value provided for {value_type!r}: {original_value!r}')