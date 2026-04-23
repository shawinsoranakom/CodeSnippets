async def get_apps_json():
        """Get the apps.json file."""
        new_templates: list = []
        default_templates: list = []
        widgets = await get_widgets()

        if not os.path.exists(APPS_PATH):
            apps_dir = os.path.dirname(APPS_PATH)
            if not os.path.exists(apps_dir):
                os.makedirs(apps_dir, exist_ok=True)
            # Write an empty file for the user to add exported apps from Workspace to.
            with open(APPS_PATH, "w", encoding="utf-8") as templates_file:
                templates_file.write(json.dumps([]))

        if os.path.exists(DEFAULT_APPS_PATH):
            with open(DEFAULT_APPS_PATH, encoding="utf-8") as f:
                default_templates = json.load(f)

        if has_additional_apps(app):
            additional_apps = await get_additional_apps(app)

            if additional_apps:
                for apps in additional_apps.values():
                    if not apps:
                        continue
                    if apps and isinstance(apps, list):
                        default_templates.extend(apps)
                    elif apps and not isinstance(apps, list):
                        logger.error(
                            "TypeError: Invalid apps.json format. Expected a list[dict] got %s instead -> %s",
                            type(apps),
                            str(apps),
                        )

        if os.path.exists(APPS_PATH):
            with open(APPS_PATH, encoding="utf-8") as templates_file:
                templates = json.load(templates_file)

            if isinstance(templates, dict):
                templates = [templates]

            templates.extend(default_templates)

            for template in templates:
                if _id := template.get("id"):
                    if _id in widgets and template not in new_templates:
                        new_templates.append(template)
                        continue
                elif template.get("layout") or template.get("tabs"):
                    if _tabs := template.get("tabs"):
                        for v in _tabs.values():
                            if v.get("layout", []) and all(
                                item.get("i", "").startswith("rich_note")
                                or item.get("i") in widgets_json
                                for item in v.get("layout")
                            ):
                                new_templates.append(template)
                                break
                    elif (
                        template.get("layout")
                        and all(
                            item.get("i", "").startswith("rich_note")
                            or item.get("i") in widgets_json
                            for item in template["layout"]
                        )
                        and template not in new_templates
                    ):
                        new_templates.append(template)

            if new_templates:
                return JSONResponse(content=new_templates, headers=obb_headers)

        return JSONResponse(content=[], headers=obb_headers)