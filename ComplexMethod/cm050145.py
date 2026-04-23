def _convert_inline_images_to_urls(self, html_content):
        """
        Find inline base64 encoded images, make an attachement out of
        them and replace the inline image with an url to the attachement.
        Find VML v:image elements, crop their source images, make an attachement
        out of them and replace their source with an url to the attachement.
        """
        root = lxml.html.fromstring(html_content)
        did_modify_body = False

        conversion_info = []  # list of tuples (image: base64 image, node: lxml node, old_url: string or None, original_id))
        with requests.Session() as session:
            for node in root.iter(lxml.etree.Element, lxml.etree.Comment):
                if node.tag == 'img':
                    # Convert base64 images in img tags to attachments.
                    match = image_re.match(node.attrib.get('src', ''))
                    if match:
                        image = match.group(2).encode()  # base64 image as bytes
                        conversion_info.append((image, node, None, int(node.attrib.get('data-original-id') or "0")))
                elif 'base64' in (node.attrib.get('style') or ''):
                    # Convert base64 images in inline styles to attachments.
                    for match in re.findall(r'data:image/[A-Za-z]+;base64,.+?(?=&\#34;|\"|\'|&quot;|\))', node.attrib.get('style')):
                        image = re.sub(r'data:image/[A-Za-z]+;base64,', '', match).encode()  # base64 image as bytes
                        conversion_info.append((image, node, match, int(node.attrib.get('data-original-id') or "0")))
                elif mso_re.match(node.text or ''):
                    # Convert base64 images (in img tags or inline styles) in mso comments to attachments.
                    base64_in_element_regex = re.compile(r"""
                        (?:(?!^)|<)[^<>]*?(data:image/[A-Za-z]+;base64,[^<]+?)(?=&\#34;|\"|'|&quot;|\))(?=[^<]+>)
                    """, re.VERBOSE)
                    for match in re.findall(base64_in_element_regex, node.text):
                        image = re.sub(r'data:image/[A-Za-z]+;base64,', '', match).encode()  # base64 image as bytes
                        conversion_info.append((image, node, match, int(node.attrib.get('data-original-id') or "0")))
                    # Crop VML images.
                    for match in re.findall(r'<v:image[^>]*>', node.text):
                        url = re.search(r'src=\s*\"([^\"]+)\"', match)[1]
                        # Make sure we have an absolute URL by adding a scheme and host if needed.
                        absolute_url = url if '//' in url else f"{self.get_base_url()}{url if url.startswith('/') else f'/{url}'}"
                        target_width_match = re.search(r'width:\s*([0-9\.]+)\s*px', match)
                        target_height_match = re.search(r'height:\s*([0-9\.]+)\s*px', match)
                        if target_width_match and target_height_match:
                            target_width = float(target_width_match[1])
                            target_height = float(target_height_match[1])
                            try:
                                image = self._get_image_by_url(absolute_url, session)
                            except (ImportValidationError, UnidentifiedImageError):
                                # Url invalid or doesn't resolve to a valid image.
                                # Note: We choose to ignore errors so as not to
                                # break the entire process just for one image's
                                # responsive cropping behavior).
                                pass
                            else:
                                image_processor = ImageProcess(image)
                                image = image_processor.crop_resize(target_width, target_height, 0, 0)
                                conversion_info.append((base64.b64encode(image.source), node, url, int(node.attrib.get('data-original-id') or "0")))

        # Apply the changes.
        urls = self._create_attachments_from_inline_images([(image, original_id) for (image, _, _, original_id) in conversion_info])
        for ((_image, node, old_url, _original_id), new_url) in zip(conversion_info, urls):
            did_modify_body = True
            if node.tag == 'img':
                node.attrib['src'] = new_url
            elif 'base64' in (node.attrib.get('style') or ''):
                node.attrib['style'] = node.attrib['style'].replace(old_url, new_url)
            else:
                node.text = node.text.replace(old_url, new_url)

        if did_modify_body:
            return lxml.html.tostring(root, encoding='unicode')
        return html_content