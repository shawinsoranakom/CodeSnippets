async def abuild_component_menu_list(self, file_paths):
        response = {"menu": []}
        await logger.adebug("-------------------- Async Building component menu list --------------------")

        tasks = [self.process_file_async(file_path) for file_path in file_paths]
        results = await asyncio.gather(*tasks)

        for file_path, (validation_result, result_content) in zip(file_paths, results, strict=True):
            file_path_ = Path(file_path)
            menu_name = file_path_.parent.name
            filename = file_path_.name

            if not validation_result:
                await logger.aerror(f"Error while processing file {file_path}")

            menu_result = self.find_menu(response, menu_name) or {
                "name": menu_name,
                "path": str(file_path_.parent),
                "components": [],
            }
            component_name = filename.split(".")[0]

            if "_" in component_name:
                component_name_camelcase = " ".join(word.title() for word in component_name.split("_"))
            else:
                component_name_camelcase = component_name

            if validation_result:
                try:
                    output_types = await asyncio.to_thread(self.get_output_types_from_code, result_content)
                except Exception:  # noqa: BLE001
                    await logger.aexception("Error while getting output types from code")
                    output_types = [component_name_camelcase]
            else:
                output_types = [component_name_camelcase]

            component_info = {
                "name": component_name_camelcase,
                "output_types": output_types,
                "file": filename,
                "code": result_content if validation_result else "",
                "error": "" if validation_result else result_content,
            }
            menu_result["components"].append(component_info)

            if menu_result not in response["menu"]:
                response["menu"].append(menu_result)

        await logger.adebug("-------------------- Component menu list built --------------------")
        return response