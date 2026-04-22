def marshall(
    proto: VegaLiteChartProto,
    data: "Data" = None,
    spec: Optional[Dict[str, Any]] = None,
    use_container_width: bool = False,
    **kwargs: Any,
) -> None:
    """Construct a Vega-Lite chart object.

    See DeltaGenerator._legacy_vega_lite_chart for docs.
    """
    # Support passing data inside spec['datasets'] and spec['data'].
    # (The data gets pulled out of the spec dict later on.)
    if isinstance(data, dict) and spec is None:
        spec = data
        data = None

    # Support passing no spec arg, but filling it with kwargs.
    # Example:
    #   marshall(proto, baz='boz')
    if spec is None:
        spec = dict()
    else:
        # Clone the spec dict, since we may be mutating it.
        spec = dict(spec)

    # Support passing in kwargs. Example:
    #   marshall(proto, {foo: 'bar'}, baz='boz')
    if len(kwargs):
        # Merge spec with unflattened kwargs, where kwargs take precedence.
        # This only works for string keys, but kwarg keys are strings anyways.
        spec = dict(spec, **dicttools.unflatten(kwargs, _CHANNELS))

    if len(spec) == 0:
        raise ValueError("Vega-Lite charts require a non-empty spec dict.")

    if "autosize" not in spec:
        spec["autosize"] = {"type": "fit", "contains": "padding"}

    # Pull data out of spec dict when it's in a 'dataset' key:
    #   marshall(proto, {datasets: {foo: df1, bar: df2}, ...})
    if "datasets" in spec:
        for k, v in spec["datasets"].items():
            dataset = proto.datasets.add()
            dataset.name = str(k)
            dataset.has_name = True
            data_frame.marshall_data_frame(v, dataset.data)
        del spec["datasets"]

    # Pull data out of spec dict when it's in a top-level 'data' key:
    #   marshall(proto, {data: df})
    #   marshall(proto, {data: {values: df, ...}})
    #   marshall(proto, {data: {url: 'url'}})
    #   marshall(proto, {data: {name: 'foo'}})
    if "data" in spec:
        data_spec = spec["data"]

        if isinstance(data_spec, dict):
            if "values" in data_spec:
                data = data_spec["values"]
                del spec["data"]
        else:
            data = data_spec
            del spec["data"]

    proto.spec = json.dumps(spec)
    proto.use_container_width = use_container_width

    if data is not None:
        data_frame.marshall_data_frame(data, proto.data)