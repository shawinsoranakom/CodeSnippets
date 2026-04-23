def create_hypernetwork(name, enable_sizes, overwrite_old, layer_structure=None, activation_func=None, weight_init=None, add_layer_norm=False, use_dropout=False, dropout_structure=None):
    # Remove illegal characters from name.
    name = "".join( x for x in name if (x.isalnum() or x in "._- "))
    assert name, "Name cannot be empty!"

    fn = os.path.join(shared.cmd_opts.hypernetwork_dir, f"{name}.pt")
    if not overwrite_old:
        assert not os.path.exists(fn), f"file {fn} already exists"

    if type(layer_structure) == str:
        layer_structure = [float(x.strip()) for x in layer_structure.split(",")]

    if use_dropout and dropout_structure and type(dropout_structure) == str:
        dropout_structure = [float(x.strip()) for x in dropout_structure.split(",")]
    else:
        dropout_structure = [0] * len(layer_structure)

    hypernet = modules.hypernetworks.hypernetwork.Hypernetwork(
        name=name,
        enable_sizes=[int(x) for x in enable_sizes],
        layer_structure=layer_structure,
        activation_func=activation_func,
        weight_init=weight_init,
        add_layer_norm=add_layer_norm,
        use_dropout=use_dropout,
        dropout_structure=dropout_structure
    )
    hypernet.save(fn)

    shared.reload_hypernetworks()