def get_storage_info(storage):
    if not isinstance(storage, torch.utils.show_pickle.FakeObject):
        raise AssertionError(f"storage is not FakeObject: {type(storage)}")
    if storage.module != "pers":
        raise AssertionError(f"storage.module is not 'pers': {storage.module!r}")
    if storage.name != "obj":
        raise AssertionError(f"storage.name is not 'obj': {storage.name!r}")
    if storage.state is not None:
        raise AssertionError(f"storage.state is not None: {storage.state!r}")
    if not isinstance(storage.args, tuple):
        raise AssertionError(f"storage.args is not a tuple: {type(storage.args)}")
    if len(storage.args) != 1:
        raise AssertionError(f"len(storage.args) is not 1: {len(storage.args)}")
    sa = storage.args[0]
    if not isinstance(sa, tuple):
        raise AssertionError(f"sa is not a tuple: {type(sa)}")
    if len(sa) != 5:
        raise AssertionError(f"len(sa) is not 5: {len(sa)}")
    if sa[0] != "storage":
        raise AssertionError(f"sa[0] is not 'storage': {sa[0]!r}")
    if not isinstance(sa[1], torch.utils.show_pickle.FakeClass):
        raise AssertionError(f"sa[1] is not FakeClass: {type(sa[1])}")
    if sa[1].module != "torch":
        raise AssertionError(f"sa[1].module is not 'torch': {sa[1].module!r}")
    if not sa[1].name.endswith("Storage"):
        raise AssertionError(f"sa[1].name does not end with 'Storage': {sa[1].name!r}")
    storage_info = [sa[1].name.replace("Storage", "")] + list(sa[2:])
    return storage_info