async def execute_step(step: str, page: Page, browser_ctx: BrowserContext, accessibility_tree: list):
    step = step.strip()
    func = step.split("[")[0].strip() if "[" in step else step.split()[0].strip()
    if func == "None":
        return ""
    elif func == "click":
        match = re.search(r"click ?\[(\d+)\]", step)
        if not match:
            raise ValueError(f"Invalid click action {step}")
        element_id = match.group(1)
        await click_element(page, get_backend_node_id(element_id, accessibility_tree))
    elif func == "hover":
        match = re.search(r"hover ?\[(\d+)\]", step)
        if not match:
            raise ValueError(f"Invalid hover action {step}")
        element_id = match.group(1)
        await hover_element(page, get_backend_node_id(element_id, accessibility_tree))
    elif func == "type":
        # add default enter flag
        if not (step.endswith("[0]") or step.endswith("[1]")):
            step += " [1]"

        match = re.search(r"type ?\[(\d+)\] ?\[(.+)\] ?\[(\d+)\]", step)
        if not match:
            raise ValueError(f"Invalid type action {step}")
        element_id, text, enter_flag = (
            match.group(1),
            match.group(2),
            match.group(3),
        )
        if enter_flag == "1":
            text += "\n"
        await click_element(page, get_backend_node_id(element_id, accessibility_tree))
        await type_text(page, text)
    elif func == "press":
        match = re.search(r"press ?\[(.+)\]", step)
        if not match:
            raise ValueError(f"Invalid press action {step}")
        key = match.group(1)
        await key_press(page, key)
    elif func == "scroll":
        # up or down
        match = re.search(r"scroll ?\[?(up|down)\]?", step)
        if not match:
            raise ValueError(f"Invalid scroll action {step}")
        direction = match.group(1)
        await scroll_page(page, direction)
    elif func == "goto":
        match = re.search(r"goto ?\[(.+)\]", step)
        if not match:
            raise ValueError(f"Invalid goto action {step}")
        url = match.group(1)
        await page.goto(url)
    elif func == "new_tab":
        page = await browser_ctx.new_page()
    elif func == "go_back":
        await page.go_back()
    elif func == "go_forward":
        await page.go_forward()
    elif func == "tab_focus":
        match = re.search(r"tab_focus ?\[(\d+)\]", step)
        if not match:
            raise ValueError(f"Invalid tab_focus action {step}")
        page_number = int(match.group(1))
        page = browser_ctx.pages[page_number]
        await page.bring_to_front()
    elif func == "close_tab":
        await page.close()
        if len(browser_ctx.pages) > 0:
            page = browser_ctx.pages[-1]
        else:
            page = await browser_ctx.new_page()
    elif func == "stop":
        match = re.search(r'stop\(?"(.+)?"\)', step)
        answer = match.group(1) if match else ""
        return answer
    else:
        raise ValueError
    await page.wait_for_load_state("domcontentloaded")
    return page