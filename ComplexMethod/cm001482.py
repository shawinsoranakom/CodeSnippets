def infotext_pasted(infotext, params):
    if "AddNet Module 1" in [x[1] for x in scripts.scripts_txt2img.infotext_fields]:
        return  # if the other extension is active, it will handle those fields, no need to do anything

    added = []

    for k in params:
        if not k.startswith("AddNet Model "):
            continue

        num = k[13:]

        if params.get("AddNet Module " + num) != "LoRA":
            continue

        name = params.get("AddNet Model " + num)
        if name is None:
            continue

        m = re_network_name.match(name)
        if m:
            name = m.group(1)

        multiplier = params.get("AddNet Weight A " + num, "1.0")

        added.append(f"<lora:{name}:{multiplier}>")

    if added:
        params["Prompt"] += "\n" + "".join(added)