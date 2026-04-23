def _get_or_create_dataset(datasets_proto, name):
    for dataset in datasets_proto:
        if dataset.has_name and dataset.name == name:
            return dataset.data

    dataset = datasets_proto.add()
    dataset.name = name
    dataset.has_name = True
    return dataset.data