def run(self, p, x_type, x_values, x_values_dropdown, y_type, y_values, y_values_dropdown, z_type, z_values, z_values_dropdown, draw_legend, include_lone_images, include_sub_grids, no_fixed_seeds, vary_seeds_x, vary_seeds_y, vary_seeds_z, margin_size, csv_mode):
        x_type, y_type, z_type = x_type or 0, y_type or 0, z_type or 0  # if axle type is None set to 0

        if not no_fixed_seeds:
            modules.processing.fix_seed(p)

        if not opts.return_grid:
            p.batch_size = 1

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

        x_opt = self.current_axis_options[x_type]
        if x_opt.choices is not None and not csv_mode:
            x_values = list_to_csv_string(x_values_dropdown)
        xs = process_axis(x_opt, x_values, x_values_dropdown)

        y_opt = self.current_axis_options[y_type]
        if y_opt.choices is not None and not csv_mode:
            y_values = list_to_csv_string(y_values_dropdown)
        ys = process_axis(y_opt, y_values, y_values_dropdown)

        z_opt = self.current_axis_options[z_type]
        if z_opt.choices is not None and not csv_mode:
            z_values = list_to_csv_string(z_values_dropdown)
        zs = process_axis(z_opt, z_values, z_values_dropdown)

        # this could be moved to common code, but unlikely to be ever triggered anywhere else
        Image.MAX_IMAGE_PIXELS = None  # disable check in Pillow and rely on check below to allow large custom image sizes
        grid_mp = round(len(xs) * len(ys) * len(zs) * p.width * p.height / 1000000)
        assert grid_mp < opts.img_max_size_mp, f'Error: Resulting grid would be too large ({grid_mp} MPixels) (max configured size is {opts.img_max_size_mp} MPixels)'

        def fix_axis_seeds(axis_opt, axis_list):
            if axis_opt.label in ['Seed', 'Var. seed']:
                return [int(random.randrange(4294967294)) if val is None or val == '' or val == -1 else val for val in axis_list]
            else:
                return axis_list

        if not no_fixed_seeds:
            xs = fix_axis_seeds(x_opt, xs)
            ys = fix_axis_seeds(y_opt, ys)
            zs = fix_axis_seeds(z_opt, zs)

        if x_opt.label == 'Steps':
            total_steps = sum(xs) * len(ys) * len(zs)
        elif y_opt.label == 'Steps':
            total_steps = sum(ys) * len(xs) * len(zs)
        elif z_opt.label == 'Steps':
            total_steps = sum(zs) * len(xs) * len(ys)
        else:
            total_steps = p.steps * len(xs) * len(ys) * len(zs)

        if isinstance(p, StableDiffusionProcessingTxt2Img) and p.enable_hr:
            if x_opt.label == "Hires steps":
                total_steps += sum(xs) * len(ys) * len(zs)
            elif y_opt.label == "Hires steps":
                total_steps += sum(ys) * len(xs) * len(zs)
            elif z_opt.label == "Hires steps":
                total_steps += sum(zs) * len(xs) * len(ys)
            elif p.hr_second_pass_steps:
                total_steps += p.hr_second_pass_steps * len(xs) * len(ys) * len(zs)
            else:
                total_steps *= 2

        total_steps *= p.n_iter

        image_cell_count = p.n_iter * p.batch_size
        cell_console_text = f"; {image_cell_count} images per cell" if image_cell_count > 1 else ""
        plural_s = 's' if len(zs) > 1 else ''
        print(f"X/Y/Z plot will create {len(xs) * len(ys) * len(zs) * image_cell_count} images on {len(zs)} {len(xs)}x{len(ys)} grid{plural_s}{cell_console_text}. (Total steps to process: {total_steps})")
        shared.total_tqdm.updateTotal(total_steps)

        state.xyz_plot_x = AxisInfo(x_opt, xs)
        state.xyz_plot_y = AxisInfo(y_opt, ys)
        state.xyz_plot_z = AxisInfo(z_opt, zs)

        # If one of the axes is very slow to change between (like SD model
        # checkpoint), then make sure it is in the outer iteration of the nested
        # `for` loop.
        first_axes_processed = 'z'
        second_axes_processed = 'y'
        if x_opt.cost > y_opt.cost and x_opt.cost > z_opt.cost:
            first_axes_processed = 'x'
            if y_opt.cost > z_opt.cost:
                second_axes_processed = 'y'
            else:
                second_axes_processed = 'z'
        elif y_opt.cost > x_opt.cost and y_opt.cost > z_opt.cost:
            first_axes_processed = 'y'
            if x_opt.cost > z_opt.cost:
                second_axes_processed = 'x'
            else:
                second_axes_processed = 'z'
        elif z_opt.cost > x_opt.cost and z_opt.cost > y_opt.cost:
            first_axes_processed = 'z'
            if x_opt.cost > y_opt.cost:
                second_axes_processed = 'x'
            else:
                second_axes_processed = 'y'

        grid_infotext = [None] * (1 + len(zs))

        def cell(x, y, z, ix, iy, iz):
            if shared.state.interrupted or state.stopping_generation:
                return Processed(p, [], p.seed, "")

            pc = copy(p)
            pc.styles = pc.styles[:]
            x_opt.apply(pc, x, xs)
            y_opt.apply(pc, y, ys)
            z_opt.apply(pc, z, zs)

            xdim = len(xs) if vary_seeds_x else 1
            ydim = len(ys) if vary_seeds_y else 1

            if vary_seeds_x:
                pc.seed += ix
            if vary_seeds_y:
                pc.seed += iy * xdim
            if vary_seeds_z:
                pc.seed += iz * xdim * ydim

            try:
                res = process_images(pc)
            except Exception as e:
                errors.display(e, "generating image for xyz plot")

                res = Processed(p, [], p.seed, "")

            # Sets subgrid infotexts
            subgrid_index = 1 + iz
            if grid_infotext[subgrid_index] is None and ix == 0 and iy == 0:
                pc.extra_generation_params = copy(pc.extra_generation_params)
                pc.extra_generation_params['Script'] = self.title()

                if x_opt.label != 'Nothing':
                    pc.extra_generation_params["X Type"] = x_opt.label
                    pc.extra_generation_params["X Values"] = x_values
                    if x_opt.label in ["Seed", "Var. seed"] and not no_fixed_seeds:
                        pc.extra_generation_params["Fixed X Values"] = ", ".join([str(x) for x in xs])

                if y_opt.label != 'Nothing':
                    pc.extra_generation_params["Y Type"] = y_opt.label
                    pc.extra_generation_params["Y Values"] = y_values
                    if y_opt.label in ["Seed", "Var. seed"] and not no_fixed_seeds:
                        pc.extra_generation_params["Fixed Y Values"] = ", ".join([str(y) for y in ys])

                grid_infotext[subgrid_index] = processing.create_infotext(pc, pc.all_prompts, pc.all_seeds, pc.all_subseeds)

            # Sets main grid infotext
            if grid_infotext[0] is None and ix == 0 and iy == 0 and iz == 0:
                pc.extra_generation_params = copy(pc.extra_generation_params)

                if z_opt.label != 'Nothing':
                    pc.extra_generation_params["Z Type"] = z_opt.label
                    pc.extra_generation_params["Z Values"] = z_values
                    if z_opt.label in ["Seed", "Var. seed"] and not no_fixed_seeds:
                        pc.extra_generation_params["Fixed Z Values"] = ", ".join([str(z) for z in zs])

                grid_infotext[0] = processing.create_infotext(pc, pc.all_prompts, pc.all_seeds, pc.all_subseeds)

            return res

        with SharedSettingsStackHelper():
            processed = draw_xyz_grid(
                p,
                xs=xs,
                ys=ys,
                zs=zs,
                x_labels=[x_opt.format_value(p, x_opt, x) for x in xs],
                y_labels=[y_opt.format_value(p, y_opt, y) for y in ys],
                z_labels=[z_opt.format_value(p, z_opt, z) for z in zs],
                cell=cell,
                draw_legend=draw_legend,
                include_lone_images=include_lone_images,
                include_sub_grids=include_sub_grids,
                first_axes_processed=first_axes_processed,
                second_axes_processed=second_axes_processed,
                margin_size=margin_size
            )

        if not processed.images:
            # It broke, no further handling needed.
            return processed

        z_count = len(zs)

        # Set the grid infotexts to the real ones with extra_generation_params (1 main grid + z_count sub-grids)
        processed.infotexts[:1 + z_count] = grid_infotext[:1 + z_count]

        if not include_lone_images:
            # Don't need sub-images anymore, drop from list:
            processed.images = processed.images[:z_count + 1]

        if opts.grid_save:
            # Auto-save main and sub-grids:
            grid_count = z_count + 1 if z_count > 1 else 1
            for g in range(grid_count):
                # TODO: See previous comment about intentional data misalignment.
                adj_g = g - 1 if g > 0 else g
                images.save_image(processed.images[g], p.outpath_grids, "xyz_grid", info=processed.infotexts[g], extension=opts.grid_format, prompt=processed.all_prompts[adj_g], seed=processed.all_seeds[adj_g], grid=True, p=processed)
                if not include_sub_grids:  # if not include_sub_grids then skip saving after the first grid
                    break

        if not include_sub_grids:
            # Done with sub-grids, drop all related information:
            for _ in range(z_count):
                del processed.images[1]
                del processed.all_prompts[1]
                del processed.all_seeds[1]
                del processed.infotexts[1]

        return processed