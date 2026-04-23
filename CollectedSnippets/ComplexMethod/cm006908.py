def build_component_menu_list(self, file_paths):
        """Build a list of menus with their components from the .py files in the directory."""
        response = {"menu": []}
        logger.debug("-------------------- Building component menu list --------------------")

        for file_path in file_paths:
            file_path_ = Path(file_path)
            menu_name = file_path_.parent.name
            filename = file_path_.name
            validation_result, result_content = self.process_file(file_path)
            if not validation_result:
                logger.error(f"Error while processing file {file_path}")

            menu_result = self.find_menu(response, menu_name) or {
                "name": menu_name,
                "path": str(file_path_.parent),
                "components": [],
            }
            component_name = filename.split(".")[0]
            # This is the name of the file which will be displayed in the UI
            # We need to change it from snake_case to CamelCase

            # first check if it's already CamelCase
            if "_" in component_name:
                component_name_camelcase = " ".join(word.title() for word in component_name.split("_"))
            else:
                component_name_camelcase = component_name

            if validation_result:
                try:
                    output_types = self.get_output_types_from_code(result_content)
                except Exception:  # noqa: BLE001
                    logger.debug("Error while getting output types from code", exc_info=True)
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
        logger.debug("-------------------- Component menu list built --------------------")
        return response