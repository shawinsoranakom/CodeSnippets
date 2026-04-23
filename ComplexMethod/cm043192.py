def score_image_for_usefulness(img, base_url, index, images_count):
            # Function to parse image height/width value and units
            """
            Scores an HTML image element for usefulness based on size, format, attributes, and position.

            The function evaluates an image's dimensions, file format, alt text, and its position among all images on the page to assign a usefulness score. Higher scores indicate images that are likely more relevant or informative for content extraction or summarization.

            Args:
                img: The HTML image element to score.
                base_url: The base URL used to resolve relative image sources.
                index: The position of the image in the list of images on the page (zero-based).
                images_count: The total number of images on the page.

            Returns:
                An integer usefulness score for the image.
            """
            def parse_dimension(dimension):
                if dimension:
                    match = re.match(r"(\d+)(\D*)", dimension)
                    if match:
                        number = int(match.group(1))
                        unit = (
                            match.group(2) or "px"
                        )  # Default unit is 'px' if not specified
                        return number, unit
                return None, None

            # Fetch image file metadata to extract size and extension
            def fetch_image_file_size(img, base_url):
                # If src is relative path construct full URL, if not it may be CDN URL
                """
                Fetches the file size of an image by sending a HEAD request to its URL.

                Args:
                    img: A BeautifulSoup tag representing the image element.
                    base_url: The base URL to resolve relative image sources.

                Returns:
                    The value of the "Content-Length" header as a string if available, otherwise None.
                """
                img_url = urljoin(base_url, img.get("src"))
                try:
                    response = requests.head(img_url)
                    if response.status_code == 200:
                        return response.headers.get("Content-Length", None)
                    else:
                        print(f"Failed to retrieve file size for {img_url}")
                        return None
                except InvalidSchema:
                    return None

            image_height = img.get("height")
            height_value, height_unit = parse_dimension(image_height)
            image_width = img.get("width")
            width_value, width_unit = parse_dimension(image_width)
            image_size = 0  # int(fetch_image_file_size(img,base_url) or 0)
            image_format = os.path.splitext(img.get("src", ""))[1].lower()
            # Remove . from format
            image_format = image_format.strip(".")
            score = 0
            if height_value:
                if height_unit == "px" and height_value > 150:
                    score += 1
                if height_unit in ["%", "vh", "vmin", "vmax"] and height_value > 30:
                    score += 1
            if width_value:
                if width_unit == "px" and width_value > 150:
                    score += 1
                if width_unit in ["%", "vh", "vmin", "vmax"] and width_value > 30:
                    score += 1
            if image_size > 10000:
                score += 1
            if img.get("alt") != "":
                score += 1
            if any(image_format == format for format in ["jpg", "png", "webp"]):
                score += 1
            if index / images_count < 0.5:
                score += 1
            return score