def parse_generation_parameters(x: str, skip_fields: list[str] | None = None):
    """parses generation parameters string, the one you see in text field under the picture in UI:
```
girl with an artist's beret, determined, blue eyes, desert scene, computer monitors, heavy makeup, by Alphonse Mucha and Charlie Bowater, ((eyeshadow)), (coquettish), detailed, intricate
Negative prompt: ugly, fat, obese, chubby, (((deformed))), [blurry], bad anatomy, disfigured, poorly drawn face, mutation, mutated, (extra_limb), (ugly), (poorly drawn hands), messy drawing
Steps: 20, Sampler: Euler a, CFG scale: 7, Seed: 965400086, Size: 512x512, Model hash: 45dee52b
```

    returns a dict with field values
    """
    if skip_fields is None:
        skip_fields = shared.opts.infotext_skip_pasting

    res = {}

    prompt = ""
    negative_prompt = ""

    done_with_prompt = False

    *lines, lastline = x.strip().split("\n")
    if len(re_param.findall(lastline)) < 3:
        lines.append(lastline)
        lastline = ''

    for line in lines:
        line = line.strip()
        if line.startswith("Negative prompt:"):
            done_with_prompt = True
            line = line[16:].strip()
        if done_with_prompt:
            negative_prompt += ("" if negative_prompt == "" else "\n") + line
        else:
            prompt += ("" if prompt == "" else "\n") + line

    for k, v in re_param.findall(lastline):
        try:
            if v[0] == '"' and v[-1] == '"':
                v = unquote(v)

            m = re_imagesize.match(v)
            if m is not None:
                res[f"{k}-1"] = m.group(1)
                res[f"{k}-2"] = m.group(2)
            else:
                res[k] = v
        except Exception:
            print(f"Error parsing \"{k}: {v}\"")

    # Extract styles from prompt
    if shared.opts.infotext_styles != "Ignore":
        found_styles, prompt_no_styles, negative_prompt_no_styles = shared.prompt_styles.extract_styles_from_prompt(prompt, negative_prompt)

        same_hr_styles = True
        if ("Hires prompt" in res or "Hires negative prompt" in res) and (infotext_ver > infotext_versions.v180_hr_styles if (infotext_ver := infotext_versions.parse_version(res.get("Version"))) else True):
            hr_prompt, hr_negative_prompt = res.get("Hires prompt", prompt), res.get("Hires negative prompt", negative_prompt)
            hr_found_styles, hr_prompt_no_styles, hr_negative_prompt_no_styles = shared.prompt_styles.extract_styles_from_prompt(hr_prompt, hr_negative_prompt)
            if same_hr_styles := found_styles == hr_found_styles:
                res["Hires prompt"] = '' if hr_prompt_no_styles == prompt_no_styles else hr_prompt_no_styles
                res['Hires negative prompt'] = '' if hr_negative_prompt_no_styles == negative_prompt_no_styles else hr_negative_prompt_no_styles

        if same_hr_styles:
            prompt, negative_prompt = prompt_no_styles, negative_prompt_no_styles
            if (shared.opts.infotext_styles == "Apply if any" and found_styles) or shared.opts.infotext_styles == "Apply":
                res['Styles array'] = found_styles

    res["Prompt"] = prompt
    res["Negative prompt"] = negative_prompt

    # Missing CLIP skip means it was set to 1 (the default)
    if "Clip skip" not in res:
        res["Clip skip"] = "1"

    hypernet = res.get("Hypernet", None)
    if hypernet is not None:
        res["Prompt"] += f"""<hypernet:{hypernet}:{res.get("Hypernet strength", "1.0")}>"""

    if "Hires resize-1" not in res:
        res["Hires resize-1"] = 0
        res["Hires resize-2"] = 0

    if "Hires sampler" not in res:
        res["Hires sampler"] = "Use same sampler"

    if "Hires schedule type" not in res:
        res["Hires schedule type"] = "Use same scheduler"

    if "Hires checkpoint" not in res:
        res["Hires checkpoint"] = "Use same checkpoint"

    if "Hires prompt" not in res:
        res["Hires prompt"] = ""

    if "Hires negative prompt" not in res:
        res["Hires negative prompt"] = ""

    if "Mask mode" not in res:
        res["Mask mode"] = "Inpaint masked"

    if "Masked content" not in res:
        res["Masked content"] = 'original'

    if "Inpaint area" not in res:
        res["Inpaint area"] = "Whole picture"

    if "Masked area padding" not in res:
        res["Masked area padding"] = 32

    restore_old_hires_fix_params(res)

    # Missing RNG means the default was set, which is GPU RNG
    if "RNG" not in res:
        res["RNG"] = "GPU"

    if "Schedule type" not in res:
        res["Schedule type"] = "Automatic"

    if "Schedule max sigma" not in res:
        res["Schedule max sigma"] = 0

    if "Schedule min sigma" not in res:
        res["Schedule min sigma"] = 0

    if "Schedule rho" not in res:
        res["Schedule rho"] = 0

    if "VAE Encoder" not in res:
        res["VAE Encoder"] = "Full"

    if "VAE Decoder" not in res:
        res["VAE Decoder"] = "Full"

    if "FP8 weight" not in res:
        res["FP8 weight"] = "Disable"

    if "Cache FP16 weight for LoRA" not in res and res["FP8 weight"] != "Disable":
        res["Cache FP16 weight for LoRA"] = False

    prompt_attention = prompt_parser.parse_prompt_attention(prompt)
    prompt_attention += prompt_parser.parse_prompt_attention(negative_prompt)
    prompt_uses_emphasis = len(prompt_attention) != len([p for p in prompt_attention if p[1] == 1.0 or p[0] == 'BREAK'])
    if "Emphasis" not in res and prompt_uses_emphasis:
        res["Emphasis"] = "Original"

    if "Refiner switch by sampling steps" not in res:
        res["Refiner switch by sampling steps"] = False

    infotext_versions.backcompat(res)

    for key in skip_fields:
        res.pop(key, None)

    return res