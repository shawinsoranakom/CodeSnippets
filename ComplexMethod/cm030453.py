def parse(cls, value, kwds):
        if isinstance(value, str):
            # We are translating here from the RFC language (address/mailbox)
            # to our API language (group/address).
            kwds['parse_tree'] = address_list = cls.value_parser(value)
            groups = []
            for addr in address_list.addresses:
                groups.append(Group(addr.display_name,
                                    [Address(mb.display_name or '',
                                             mb.local_part or '',
                                             mb.domain or '')
                                     for mb in addr.all_mailboxes]))
            defects = list(address_list.all_defects)
        else:
            # Assume it is Address/Group stuff
            if not hasattr(value, '__iter__'):
                value = [value]
            groups = [Group(None, [item]) if not hasattr(item, 'addresses')
                                          else item
                                    for item in value]
            defects = []
        kwds['groups'] = groups
        kwds['defects'] = defects
        kwds['decoded'] = ', '.join([str(item) for item in groups])
        if 'parse_tree' not in kwds:
            kwds['parse_tree'] = cls.value_parser(kwds['decoded'])