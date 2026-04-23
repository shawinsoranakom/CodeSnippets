def render_option_group_parsing(
        self,
        f: Function,
        template_dict: TemplateDict,
        limited_capi: bool,
    ) -> None:
        # positional only, grouped, optional arguments!
        # can be optional on the left or right.
        # here's an example:
        #
        # [ [ [ A1 A2 ] B1 B2 B3 ] C1 C2 ] D1 D2 D3 [ E1 E2 E3 [ F1 F2 F3 ] ]
        #
        # Here group D are required, and all other groups are optional.
        # (Group D's "group" is actually None.)
        # We can figure out which sets of arguments we have based on
        # how many arguments are in the tuple.
        #
        # Note that you need to count up on both sides.  For example,
        # you could have groups C+D, or C+D+E, or C+D+E+F.
        #
        # What if the number of arguments leads us to an ambiguous result?
        # Clinic prefers groups on the left.  So in the above example,
        # five arguments would map to B+C, not C+D.

        out = []
        parameters = list(f.parameters.values())
        if isinstance(parameters[0].converter, self_converter):
            del parameters[0]

        group: list[Parameter] | None = None
        left = []
        right = []
        required: list[Parameter] = []
        last: int | Literal[Sentinels.unspecified] = unspecified

        for p in parameters:
            group_id = p.group
            if group_id != last:
                last = group_id
                group = []
                if group_id < 0:
                    left.append(group)
                elif group_id == 0:
                    group = required
                else:
                    right.append(group)
            assert group is not None
            group.append(p)

        count_min = sys.maxsize
        count_max = -1

        if limited_capi:
            nargs = 'PyTuple_Size(args)'
        else:
            nargs = 'PyTuple_GET_SIZE(args)'
        out.append(f"switch ({nargs}) {{\n")
        for subset in permute_optional_groups(left, required, right):
            count = len(subset)
            count_min = min(count_min, count)
            count_max = max(count_max, count)

            if count == 0:
                out.append("""    case 0:
        break;
""")
                continue

            group_ids = {p.group for p in subset}  # eliminate duplicates
            d: dict[str, str | int] = {}
            d['count'] = count
            d['name'] = f.name
            d['format_units'] = "".join(p.converter.format_unit for p in subset)

            parse_arguments: list[str] = []
            for p in subset:
                p.converter.parse_argument(parse_arguments)
            d['parse_arguments'] = ", ".join(parse_arguments)

            group_ids.discard(0)
            lines = "\n".join([
                self.group_to_variable_name(g) + " = 1;"
                for g in group_ids
            ])

            s = """\
    case {count}:
        if (!PyArg_ParseTuple(args, "{format_units}:{name}", {parse_arguments})) {{
            goto exit;
        }}
        {group_booleans}
        break;
"""
            s = libclinic.linear_format(s, group_booleans=lines)
            s = s.format_map(d)
            out.append(s)

        out.append("    default:\n")
        s = '        PyErr_SetString(PyExc_TypeError, "{} requires {} to {} arguments");\n'
        out.append(s.format(f.full_name, count_min, count_max))
        out.append('        goto exit;\n')
        out.append("}")

        template_dict['option_group_parsing'] = libclinic.format_escape("".join(out))