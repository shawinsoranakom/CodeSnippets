def config_list(**configs):
    """Generate configs based on the list of input shapes.
    This function will take input shapes specified in a list from user. Besides
    that, all other parameters will be cross produced first and each of the
    generated list will be merged with the input shapes list.

    Reserved Args:
        attr_names(reserved): a list of names for input shapes.
        attrs(reserved): a list of values for each input shape.
        corss_product: a dictionary of attributes which will be
                       cross produced with the input shapes.
        tags(reserved): a tag used to filter inputs.

    Here is an example:
    attrs = [
        [1, 2],
        [4, 5],
    ],
    attr_names = ['M', 'N'],
    cross_product_configs={
        'device': ['cpu', 'cuda'],
    },

    we will generate [[{'M': 1}, {'N' : 2}, {'device' : 'cpu'}],
                      [{'M': 1}, {'N' : 2}, {'device' : 'cuda'}],
                      [{'M': 4}, {'N' : 5}, {'device' : 'cpu'}],
                      [{'M': 4}, {'N' : 5}, {'device' : 'cuda'}]]
    """
    generated_configs = []
    reserved_names = ["attrs", "attr_names", "tags"]
    if any(attr not in configs for attr in reserved_names):
        raise ValueError("Missing attrs in configs")

    _validate(configs)

    cross_configs = None
    if "cross_product_configs" in configs:
        cross_configs = cross_product_configs(**configs["cross_product_configs"])

    for inputs in configs["attrs"]:
        tmp_result = [
            {configs["attr_names"][i]: input_value}
            for i, input_value in enumerate(inputs)
        ]
        # TODO(mingzhe0908):
        # If multiple 'tags' were provided, do they get concat?
        # If a config has both ['short', 'medium'], it should match
        # both 'short' and 'medium' tag-filter?
        tmp_result.append({"tags": "_".join(configs["tags"])})
        if cross_configs:
            generated_configs += [tmp_result + list(config) for config in cross_configs]
        else:
            generated_configs.append(tmp_result)

    return generated_configs