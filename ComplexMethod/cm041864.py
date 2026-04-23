def query(
        self,
        query="Describe this image. Also tell me what text is in the image, if any.",
        base_64=None,
        path=None,
        lmc=None,
        pil_image=None,
    ):
        """
        Uses Moondream to ask query of the image (which can be a base64, path, or lmc message)
        """

        if self.model == None and self.tokenizer == None:
            try:
                success = self.load(load_easyocr=False)
            except ImportError:
                print(
                    "\nTo use local vision, run `pip install 'open-interpreter[local]'`.\n"
                )
                return ""
            if not success:
                return ""

        if lmc:
            if "base64" in lmc["format"]:
                # # Extract the extension from the format, default to 'png' if not specified
                # if "." in lmc["format"]:
                #     extension = lmc["format"].split(".")[-1]
                # else:
                #     extension = "png"

                # Decode the base64 image
                img_data = base64.b64decode(lmc["content"])
                img = Image.open(io.BytesIO(img_data))

            elif lmc["format"] == "path":
                # Convert to base64
                image_path = lmc["content"]
                img = Image.open(image_path)
        elif base_64:
            img_data = base64.b64decode(base_64)
            img = Image.open(io.BytesIO(img_data))
        elif path:
            img = Image.open(path)
        elif pil_image:
            img = pil_image

        with contextlib.redirect_stdout(open(os.devnull, "w")):
            enc_image = self.model.encode_image(img)
            answer = self.model.answer_question(
                enc_image, query, self.tokenizer, max_length=400
            )

        return answer