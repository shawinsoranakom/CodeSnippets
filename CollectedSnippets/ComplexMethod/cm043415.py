def _extract_images(self, page, image_dir: Optional[Path]) -> List[Dict]:
        # Import pypdf for type checking only when needed
        try:
            from pypdf.generic import IndirectObject
        except ImportError:
            raise ImportError("pypdf is required for PDF processing. Install with 'pip install crawl4ai[pdf]'")

        if not self.extract_images:
            return []

        images = []
        try:
            resources = page.get("/Resources")
            if resources:  # Check if resources exist
                resources = resources.get_object()  # Resolve IndirectObject
                if '/XObject' in resources:
                    xobjects = resources['/XObject'].get_object()
                    img_count = 0
                    for obj_name in xobjects:
                        xobj = xobjects[obj_name]
                        if hasattr(xobj, 'get_object') and callable(xobj.get_object):
                            xobj = xobj.get_object()
                            if xobj.get('/Subtype') == '/Image':
                                try:
                                    img_count += 1
                                    img_filename = f"page_{self.current_page_number}_img_{img_count}"
                                    data = xobj.get_data()
                                    filters = xobj.get('/Filter', [])
                                    if not isinstance(filters, list):
                                        filters = [filters]

                                    # Resolve IndirectObjects in properties
                                    width = xobj.get('/Width', 0)
                                    height = xobj.get('/Height', 0)
                                    color_space = xobj.get('/ColorSpace', '/DeviceRGB')
                                    if isinstance(color_space, IndirectObject):
                                        color_space = color_space.get_object()

                                    # Handle different image encodings
                                    success = False
                                    image_format = 'bin'
                                    image_data = None

                                    if '/FlateDecode' in filters:
                                        try:
                                            decode_parms = xobj.get('/DecodeParms', {})
                                            if isinstance(decode_parms, IndirectObject):
                                                decode_parms = decode_parms.get_object()

                                            predictor = decode_parms.get('/Predictor', 1)
                                            bits = xobj.get('/BitsPerComponent', 8)
                                            colors = 3 if color_space == '/DeviceRGB' else 1

                                            if predictor >= 10:
                                                data = apply_png_predictor(data, width, bits, colors)

                                            # Create PIL Image
                                            from PIL import Image
                                            mode = 'RGB' if color_space == '/DeviceRGB' else 'L'
                                            img = Image.frombytes(mode, (width, height), data)

                                            if self.save_images_locally:
                                                final_path = (image_dir / img_filename).with_suffix('.png')
                                                img.save(final_path)
                                                image_data = str(final_path)
                                            else:
                                                import io
                                                img_byte_arr = io.BytesIO()
                                                img.save(img_byte_arr, format='PNG')
                                                image_data = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

                                            success = True
                                            image_format = 'png'
                                        except Exception as e:
                                            logger.error(f"FlateDecode error: {str(e)}")

                                    elif '/DCTDecode' in filters:
                                        # JPEG image
                                        try:
                                            if self.save_images_locally:
                                                final_path = (image_dir / img_filename).with_suffix('.jpg')
                                                with open(final_path, 'wb') as f:
                                                    f.write(data)
                                                image_data = str(final_path)
                                            else:
                                                image_data = base64.b64encode(data).decode('utf-8')
                                            success = True
                                            image_format = 'jpeg'
                                        except Exception as e:
                                            logger.error(f"JPEG save error: {str(e)}")

                                    elif '/CCITTFaxDecode' in filters:
                                        try:
                                            if data[:4] != b'II*\x00':
                                                # Add TIFF header if missing
                                                tiff_header = b'II*\x00\x08\x00\x00\x00\x0e\x00\x00\x01\x03\x00\x01\x00\x00\x00' + \
                                                            width.to_bytes(4, 'little') + \
                                                            b'\x01\x03\x00\x01\x00\x00\x00' + \
                                                            height.to_bytes(4, 'little') + \
                                                            b'\x01\x12\x00\x03\x00\x00\x00\x01\x00\x01\x00\x00\x01\x17\x00\x04\x00\x00\x00\x01\x00\x00\x00J\x01\x1B\x00\x05\x00\x00\x00\x01\x00\x00\x00R\x01\x28\x00\x03\x00\x00\x00\x01\x00\x02\x00\x00'
                                                data = tiff_header + data

                                            if self.save_images_locally:
                                                final_path = (image_dir / img_filename).with_suffix('.tiff')
                                                with open(final_path, 'wb') as f:
                                                    f.write(data)
                                                image_data = str(final_path)
                                            else:
                                                image_data = base64.b64encode(data).decode('utf-8')
                                            success = True
                                            image_format = 'tiff'
                                        except Exception as e:
                                            logger.error(f"CCITT save error: {str(e)}")

                                    elif '/JPXDecode' in filters:
                                        # JPEG 2000
                                        try:
                                            if self.save_images_locally:
                                                final_path = (image_dir / img_filename).with_suffix('.jp2')
                                                with open(final_path, 'wb') as f:
                                                    f.write(data)
                                                image_data = str(final_path)
                                            else:
                                                image_data = base64.b64encode(data).decode('utf-8')
                                            success = True
                                            image_format = 'jpeg2000'
                                        except Exception as e:
                                            logger.error(f"JPEG2000 save error: {str(e)}")

                                    if success and image_data:
                                        image_info = {
                                            "format": image_format,
                                            "width": width,
                                            "height": height,
                                            "color_space": str(color_space),
                                            "bits_per_component": xobj.get('/BitsPerComponent', 1)
                                        }

                                        if self.save_images_locally:
                                            image_info["path"] = image_data
                                        else:
                                            image_info["data"] = image_data

                                        images.append(image_info)
                                    else:
                                        # Fallback: Save raw data
                                        if self.save_images_locally:
                                            final_path = (image_dir / img_filename).with_suffix('.bin')
                                            with open(final_path, 'wb') as f:
                                                f.write(data)
                                            logger.warning(f"Saved raw image data to {final_path}")
                                        else:
                                            image_data = base64.b64encode(data).decode('utf-8')
                                            images.append({
                                                "format": "bin",
                                                "width": width,
                                                "height": height,
                                                "color_space": str(color_space),
                                                "bits_per_component": xobj.get('/BitsPerComponent', 1),
                                                "data": image_data
                                            })

                                except Exception as e:
                                    logger.error(f"Error processing image: {str(e)}")
        except Exception as e:
            logger.error(f"Image extraction error: {str(e)}")

        return images