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