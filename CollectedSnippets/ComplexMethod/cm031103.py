def dump_ctype(tp, struct_or_union_tag='', variable_name='', semi=''):
    """Get C type name or declaration of a ctype

    struct_or_union_tag: name of the struct or union
    variable_name: if given, declare the given variable
    semi: a semicolon, and/or bitfield specification to tack on to the end
    """
    requires = set()
    if issubclass(tp, (Structure, Union)):
        attributes = []
        pushes = []
        pops = []
        pack = getattr(tp, '_pack_', None)
        if pack is not None:
            pushes.append(f'#pragma pack(push, {pack})')
            pops.append(f'#pragma pack(pop)')
        layout = getattr(tp, '_layout_', None)
        if layout == 'ms':
            # The 'ms_struct' attribute only works on x86 and PowerPC
            requires.add(
                'defined(MS_WIN32) || ('
                    '(defined(__x86_64__) || defined(__i386__) || defined(__ppc64__)) && ('
                    'defined(__GNUC__) || defined(__clang__)))'
                )
            attributes.append('ms_struct')
        if attributes:
            a = f' GCC_ATTR({", ".join(attributes)})'
        else:
            a = ''
        lines = [f'{struct_or_union(tp)}{a}{maybe_space(struct_or_union_tag)} ' +'{']
        for fielddesc in tp._fields_:
            f_name, f_tp, f_bits = unpack_field_desc(*fielddesc)
            if f_name in getattr(tp, '_anonymous_', ()):
                f_name = ''
            if f_bits is None:
                subsemi = ';'
            else:
                if f_tp not in (c_int, c_uint):
                    # XLC can reportedly only handle int & unsigned int
                    # bitfields (the only types required by C spec)
                    requires.add('!defined(__xlc__)')
                subsemi = f' :{f_bits};'
            sub_lines, sub_requires = dump_ctype(
                f_tp, variable_name=f_name, semi=subsemi)
            requires.update(sub_requires)
            for line in sub_lines:
                lines.append('    ' + line)
        lines.append(f'}}{maybe_space(variable_name)}{semi}')
        return [*pushes, *lines, *reversed(pops)], requires
    else:
        return [dump_simple_ctype(tp, variable_name, semi)], requires