def run(self, p, checkbox_iterate, checkbox_iterate_batch, prompt_position, prompt_txt: str):
        lines = [x for x in (x.strip() for x in prompt_txt.splitlines()) if x]

        p.do_not_save_grid = True

        job_count = 0
        jobs = []

        for line in lines:
            if "--" in line:
                try:
                    args = cmdargs(line)
                except Exception:
                    errors.report(f"Error parsing line {line} as commandline", exc_info=True)
                    args = {"prompt": line}
            else:
                args = {"prompt": line}

            job_count += args.get("n_iter", p.n_iter)

            jobs.append(args)

        print(f"Will process {len(lines)} lines in {job_count} jobs.")
        if (checkbox_iterate or checkbox_iterate_batch) and p.seed == -1:
            p.seed = int(random.randrange(4294967294))

        state.job_count = job_count

        images = []
        all_prompts = []
        infotexts = []
        for args in jobs:
            state.job = f"{state.job_no + 1} out of {state.job_count}"

            copy_p = copy.copy(p)
            for k, v in args.items():
                if k == "sd_model":
                    copy_p.override_settings['sd_model_checkpoint'] = v
                else:
                    setattr(copy_p, k, v)

            if args.get("prompt") and p.prompt:
                if prompt_position == "start":
                    copy_p.prompt = args.get("prompt") + " " + p.prompt
                else:
                    copy_p.prompt = p.prompt + " " + args.get("prompt")

            if args.get("negative_prompt") and p.negative_prompt:
                if prompt_position == "start":
                    copy_p.negative_prompt = args.get("negative_prompt") + " " + p.negative_prompt
                else:
                    copy_p.negative_prompt = p.negative_prompt + " " + args.get("negative_prompt")

            proc = process_images(copy_p)
            images += proc.images

            if checkbox_iterate:
                p.seed = p.seed + (p.batch_size * p.n_iter)
            all_prompts += proc.all_prompts
            infotexts += proc.infotexts

        return Processed(p, images, p.seed, "", all_prompts=all_prompts, infotexts=infotexts)