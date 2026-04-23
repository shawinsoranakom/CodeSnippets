def get_discovery_info(platform_setup, groups, controller_id):
    """Get discovery info for specified IHC platform."""
    discovery_data = {}
    for group in groups:
        groupname = group.attrib["name"]
        for product_cfg in platform_setup:
            products = group.findall(product_cfg[CONF_XPATH])
            for product in products:
                product_id = int(product.attrib["id"].strip("_"), 0)
                nodes = product.findall(product_cfg[CONF_NODE])
                for node in nodes:
                    if "setting" in node.attrib and node.attrib["setting"] == "yes":
                        continue
                    ihc_id = int(node.attrib["id"].strip("_"), 0)
                    name = f"{groupname}_{ihc_id}"
                    # make the model number look a bit nicer - strip leading _
                    model = product.get("product_identifier", "").lstrip("_")
                    device = {
                        "ihc_id": ihc_id,
                        "ctrl_id": controller_id,
                        "product": {
                            "id": product_id,
                            "name": product.get("name") or "",
                            "note": product.get("note") or "",
                            "position": product.get("position") or "",
                            "model": model,
                            "group": groupname,
                        },
                        "product_cfg": product_cfg,
                    }
                    discovery_data[name] = device
    return discovery_data