def mapping(data_source, geom_name="geom", layer_key=0, multi_geom=False):
    """
    Given a DataSource, generate a dictionary that may be used
    for invoking the LayerMapping utility.

    Keyword Arguments:
     `geom_name` => The name of the geometry field to use for the model.

     `layer_key` => The key specifying which layer in the DataSource to use;
       defaults to 0 (the first layer). May be an integer index or a string
       identifier for the layer.

     `multi_geom` => Boolean (default: False) - specify as multigeometry.
    """
    if isinstance(data_source, str):
        # Instantiating the DataSource from the string.
        data_source = DataSource(data_source)
    elif isinstance(data_source, DataSource):
        pass
    else:
        raise TypeError(
            "Data source parameter must be a string or a DataSource object."
        )

    # Creating the dictionary.
    _mapping = {}

    # Generating the field name for each field in the layer.
    for field in data_source[layer_key].fields:
        mfield = field.lower()
        if mfield[-1:] == "_":
            mfield += "field"
        _mapping[mfield] = field
    gtype = data_source[layer_key].geom_type
    if multi_geom:
        gtype.to_multi()
    _mapping[geom_name] = str(gtype).upper()
    return _mapping