def process_axis(opt, vals, vals_dropdown):
            if opt.label == 'Nothing':
                return [0]

            if opt.choices is not None and not csv_mode:
                valslist = vals_dropdown
            elif opt.prepare is not None:
                valslist = opt.prepare(vals)
            else:
                valslist = csv_string_to_list_strip(vals)

            if opt.type == int:
                valslist_ext = []

                for val in valslist:
                    if val.strip() == '':
                        continue
                    m = re_range.fullmatch(val)
                    mc = re_range_count.fullmatch(val)
                    if m is not None:
                        start = int(m.group(1))
                        end = int(m.group(2)) + 1
                        step = int(m.group(3)) if m.group(3) is not None else 1

                        valslist_ext += list(range(start, end, step))
                    elif mc is not None:
                        start = int(mc.group(1))
                        end = int(mc.group(2))
                        num = int(mc.group(3)) if mc.group(3) is not None else 1

                        valslist_ext += [int(x) for x in np.linspace(start=start, stop=end, num=num).tolist()]
                    else:
                        valslist_ext.append(val)

                valslist = valslist_ext
            elif opt.type == float:
                valslist_ext = []

                for val in valslist:
                    if val.strip() == '':
                        continue
                    m = re_range_float.fullmatch(val)
                    mc = re_range_count_float.fullmatch(val)
                    if m is not None:
                        start = float(m.group(1))
                        end = float(m.group(2))
                        step = float(m.group(3)) if m.group(3) is not None else 1

                        valslist_ext += np.arange(start, end + step, step).tolist()
                    elif mc is not None:
                        start = float(mc.group(1))
                        end = float(mc.group(2))
                        num = int(mc.group(3)) if mc.group(3) is not None else 1

                        valslist_ext += np.linspace(start=start, stop=end, num=num).tolist()
                    else:
                        valslist_ext.append(val)

                valslist = valslist_ext
            elif opt.type == str_permutations:
                valslist = list(permutations(valslist))

            valslist = [opt.type(x) for x in valslist]

            # Confirm options are valid before starting
            if opt.confirm:
                opt.confirm(p, valslist)

            return valslist