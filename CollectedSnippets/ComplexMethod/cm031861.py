def merge_old_version(version, new, old):
    # Changes to exclusion file not implemented yet
    if old.exclusions != new.exclusions:
        raise NotImplementedError("exclusions differ")

    # In these change records, 0xFF means "no change"
    bidir_changes = [0xFF]*0x110000
    category_changes = [0xFF]*0x110000
    decimal_changes = [0xFF]*0x110000
    mirrored_changes = [0xFF]*0x110000
    east_asian_width_changes = [0xFF]*0x110000
    # In numeric data, 0 means "no change",
    # -1 means "did not have a numeric value
    numeric_changes = [0] * 0x110000
    # normalization_changes is a list of key-value pairs
    normalization_changes = []
    for i in range(0x110000):
        if new.table[i] is None:
            # Characters unassigned in the new version ought to
            # be unassigned in the old one
            assert old.table[i] is None
            continue
        # check characters unassigned in the old version
        if old.table[i] is None:
            # category 0 is "unassigned"
            category_changes[i] = 0
            continue
        if old.bidi_classes[i] != new.bidi_classes[i]:
            bidir_changes[i] = BIDIRECTIONAL_NAMES.index(old.bidi_classes[i])
        # check characters that differ
        if old.table[i] != new.table[i]:
            for k, field in enumerate(dataclasses.fields(UcdRecord)):
                value = getattr(old.table[i], field.name)
                new_value = getattr(new.table[i], field.name)
                if value != new_value:
                    if k == 1 and i in PUA_15:
                        # the name is not set in the old.table, but in the
                        # new.table we are using it for aliases and named seq
                        assert value == ''
                    elif k == 2:
                        category_changes[i] = CATEGORY_NAMES.index(value)
                    elif k == 4:
                        # bidi_class changes handled via bidi_classes
                        pass
                    elif k == 5:
                        # We assume that all normalization changes are in 1:1 mappings
                        assert " " not in value
                        normalization_changes.append((i, value))
                    elif k == 6:
                        # we only support changes where the old value is a single digit
                        assert value in "0123456789"
                        decimal_changes[i] = int(value)
                    elif k == 8:
                        # Since 0 encodes "no change", the old value is better not 0
                        if not value:
                            numeric_changes[i] = -1
                        else:
                            numeric_changes[i] = float(value)
                            assert numeric_changes[i] not in (0, -1)
                    elif k == 9:
                        if value == 'Y':
                            mirrored_changes[i] = '1'
                        else:
                            mirrored_changes[i] = '0'
                    elif k == 11:
                        # change to ISO comment, ignore
                        pass
                    elif k == 12:
                        # change to simple uppercase mapping; ignore
                        pass
                    elif k == 13:
                        # change to simple lowercase mapping; ignore
                        pass
                    elif k == 14:
                        # change to simple titlecase mapping; ignore
                        pass
                    elif k == 15:
                        # change to east asian width
                        east_asian_width_changes[i] = EASTASIANWIDTH_NAMES.index(value)
                    elif k == 16:
                        # derived property changes; not yet
                        pass
                    elif k == 17:
                        # normalization quickchecks are not performed
                        # for older versions
                        pass
                    elif k == 18:
                        # The Indic_Conjunct_Break property did not exist for
                        # older versions
                        pass
                    else:
                        class Difference(Exception):pass
                        raise Difference(hex(i), k, old.table[i], new.table[i])
    new.changed.append((version, list(zip(bidir_changes, category_changes,
                                          decimal_changes, mirrored_changes,
                                          east_asian_width_changes,
                                          numeric_changes)),
                        normalization_changes))