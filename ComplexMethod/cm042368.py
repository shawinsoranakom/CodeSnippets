def _parse_field(spec: Any, reader: BinaryReader, obj: Any) -> Any:
  field_type = _field_type_from_spec(spec)
  if field_type is not None:
    spec = field_type
  if isinstance(spec, ConstType):
    value = _parse_field(spec.base_type, reader, obj)
    if value != spec.expected:
      raise ValueError(f"Invalid constant: expected {spec.expected!r}, got {value!r}")
    return value
  if isinstance(spec, EnumType):
    raw = _parse_field(spec.base_type, reader, obj)
    try:
      return spec.enum_cls(raw)
    except ValueError:
      return raw
  if isinstance(spec, SwitchType):
    key = _resolve_path(obj, spec.selector)
    target = spec.cases.get(key, spec.default)
    if target is None:
      return None
    return _parse_field(target, reader, obj)
  if isinstance(spec, ArrayType):
    count = _resolve_path(obj, spec.count_field)
    return [_parse_field(spec.element_type, reader, obj) for _ in range(int(count))]
  if isinstance(spec, SubstreamType):
    length = _resolve_path(obj, spec.length_field)
    data = reader.read_bytes(int(length))
    sub_reader = BinaryReader(data)
    return _parse_field(spec.element_type, sub_reader, obj)
  if isinstance(spec, IntType):
    return reader._read_struct(_int_format(spec))
  if isinstance(spec, FloatType):
    return reader._read_struct(_float_format(spec))
  if isinstance(spec, BitsType):
    value = reader.read_bits_int_be(spec.bits)
    return bool(value) if spec.bits == 1 else value
  if isinstance(spec, BytesType):
    return reader.read_bytes(spec.size)
  if isinstance(spec, type) and issubclass(spec, BinaryStruct):
    return spec._read(reader)
  raise TypeError(f"Unsupported field spec: {spec!r}")