def test_parent_group_templating(inventory_module):
    inventory_module.inventory.add_host('cow')
    inventory_module.inventory.set_variable('cow', 'sound', 'mmmmmmmmmm')
    inventory_module.inventory.set_variable('cow', 'nickname', 'betsy')
    host = inventory_module.inventory.get_host('cow')
    keyed_groups = [
        {
            'key': 'sound',
            'prefix': 'sound',
            'parent_group': '{{ nickname }}'
        },
        {
            'key': 'nickname',
            'prefix': '',
            'separator': '',
            'parent_group': 'nickname'  # statically-named parent group, conflicting with hostvar
        },
        {
            'key': 'nickname',
            'separator': '',
            'parent_group': '{{ location | default("field") }}'
        },
        {
            # duplicate this one to ensure it doesn't show up in parents more than once
            'key': 'nickname',
            'separator': '',
            'parent_group': '{{ location | default("field") }}'
        },
        {
            'key': 'nickname',
            'prefix': 'omitted_parent',
            'parent_group': '{{ omit }}'
        }

    ]
    inventory_module._add_host_to_keyed_groups(
        _trust(keyed_groups), host.vars, host.name, strict=True
    )
    # first keyed group, "betsy" is a parent group name dynamically generated
    betsys_group = inventory_module.inventory.groups['betsy']
    assert [child.name for child in betsys_group.child_groups] == ['sound_mmmmmmmmmm']
    # second keyed group, "nickname" is a statically-named root group
    nicknames_group = inventory_module.inventory.groups['nickname']
    assert [child.name for child in nicknames_group.child_groups] == ['betsy']
    # second keyed group actually generated the parent group of the first keyed group
    assert nicknames_group.child_groups == [betsys_group]
    # assert that these are, in fact, the same object
    assert nicknames_group.child_groups[0] is betsys_group
    # "betsy" has two parents
    locations_group = inventory_module.inventory.groups['field']
    assert [child.name for child in locations_group.child_groups] == ['betsy']
    assert len(inventory_module.inventory.groups['betsy'].parent_groups) == 2
    assert set(inventory_module.inventory.groups['betsy'].parent_groups) == {locations_group, nicknames_group}