def ocr(
        self,
        base_64=None,
        path=None,
        lmc=None,
        pil_image=None,
    ):
        """
        Gets OCR of image.
        """

        if lmc:
            if "base64" in lmc["format"]:
                # # Extract the extension from the format, default to 'png' if not specified
                # if "." in lmc["format"]:
                #     extension = lmc["format"].split(".")[-1]
                # else:
                #     extension = "png"
                # Save the base64 content as a temporary file
                img_data = base64.b64decode(lmc["content"])
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".png"
                ) as temp_file:
                    temp_file.write(img_data)
                    temp_file_path = temp_file.name

                # Set path to the path of the temporary file
                path = temp_file_path

            elif lmc["format"] == "path":
                # Convert to base64
                path = lmc["content"]
        elif base_64:
            # Save the base64 content as a temporary file
            img_data = base64.b64decode(base_64)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                temp_file.write(img_data)
                temp_file_path = temp_file.name

            # Set path to the path of the temporary file
            path = temp_file_path
        elif path:
            pass
        elif pil_image:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                pil_image.save(temp_file, format="PNG")
                temp_file_path = temp_file.name

            # Set path to the path of the temporary file
            path = temp_file_path

        try:
            if not self.easyocr:
                self.load(load_moondream=False)
            result = self.easyocr.readtext(path)
            text = " ".join([item[1] for item in result])
            return text.strip()
        except ImportError:
            print(
                "\nTo use local vision, run `pip install 'open-interpreter[local]'`.\n"
            )
            return ""