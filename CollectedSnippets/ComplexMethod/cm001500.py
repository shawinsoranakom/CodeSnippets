def run(self, p, put_at_start, different_seeds, prompt_type, variations_delimiter, margin_size):
        modules.processing.fix_seed(p)
        # Raise error if promp type is not positive or negative
        if prompt_type not in ["positive", "negative"]:
            raise ValueError(f"Unknown prompt type {prompt_type}")
        # Raise error if variations delimiter is not comma or space
        if variations_delimiter not in ["comma", "space"]:
            raise ValueError(f"Unknown variations delimiter {variations_delimiter}")

        prompt = p.prompt if prompt_type == "positive" else p.negative_prompt
        original_prompt = prompt[0] if type(prompt) == list else prompt
        positive_prompt = p.prompt[0] if type(p.prompt) == list else p.prompt

        delimiter = ", " if variations_delimiter == "comma" else " "

        all_prompts = []
        prompt_matrix_parts = original_prompt.split("|")
        combination_count = 2 ** (len(prompt_matrix_parts) - 1)
        for combination_num in range(combination_count):
            selected_prompts = [text.strip().strip(',') for n, text in enumerate(prompt_matrix_parts[1:]) if combination_num & (1 << n)]

            if put_at_start:
                selected_prompts = selected_prompts + [prompt_matrix_parts[0]]
            else:
                selected_prompts = [prompt_matrix_parts[0]] + selected_prompts

            all_prompts.append(delimiter.join(selected_prompts))

        p.n_iter = math.ceil(len(all_prompts) / p.batch_size)
        p.do_not_save_grid = True

        print(f"Prompt matrix will create {len(all_prompts)} images using a total of {p.n_iter} batches.")

        if prompt_type == "positive":
            p.prompt = all_prompts
        else:
            p.negative_prompt = all_prompts
        p.seed = [p.seed + (i if different_seeds else 0) for i in range(len(all_prompts))]
        p.prompt_for_display = positive_prompt
        processed = process_images(p)

        grid = images.image_grid(processed.images, p.batch_size, rows=1 << ((len(prompt_matrix_parts) - 1) // 2))
        grid = images.draw_prompt_matrix(grid, processed.images[0].width, processed.images[0].height, prompt_matrix_parts, margin_size)
        processed.images.insert(0, grid)
        processed.index_of_first_image = 1
        processed.infotexts.insert(0, processed.infotexts[0])

        if opts.grid_save:
            images.save_image(processed.images[0], p.outpath_grids, "prompt_matrix", extension=opts.grid_format, prompt=original_prompt, seed=processed.seed, grid=True, p=p)

        return processed