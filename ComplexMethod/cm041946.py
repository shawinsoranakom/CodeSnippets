def _makeup_ui_document(self, elem_list: list[AndroidElement], docs_idr: Path, use_exist_doc: bool = True) -> str:
        if not use_exist_doc:
            return ""

        ui_doc = """
You also have access to the following documentations that describes the functionalities of UI 
elements you can interact on the screen. These docs are crucial for you to determine the target of your 
next action. You should always prioritize these documented elements for interaction: """
        for i, elem in enumerate(elem_list):
            doc_path = docs_idr.joinpath(f"{elem.uid}.txt")
            if not doc_path.exists():
                continue
            try:
                doc_content = ast.literal_eval(doc_path.read_text())
            except Exception as exp:
                logger.error(f"ast parse doc: {doc_path} failed, exp: {exp}")
                continue

            ui_doc += f"Documentation of UI element labeled with the numeric tag '{i + 1}':\n"
            if doc_content["tap"]:
                ui_doc += f"This UI element is clickable. {doc_content['tap']}\n\n"
            if doc_content["text"]:
                ui_doc += (
                    f"This UI element can receive text input. The text input is used for the following "
                    f"purposes: {doc_content['text']}\n\n"
                )
            if doc_content["long_press"]:
                ui_doc += f"This UI element is long clickable. {doc_content['long_press']}\n\n"
            if doc_content["v_swipe"]:
                ui_doc += (
                    f"This element can be swiped directly without tapping. You can swipe vertically on "
                    f"this UI element. {doc_content['v_swipe']}\n\n"
                )
            if doc_content["h_swipe"]:
                ui_doc += (
                    f"This element can be swiped directly without tapping. You can swipe horizontally on "
                    f"this UI element. {doc_content['h_swipe']}\n\n"
                )
        return ui_doc