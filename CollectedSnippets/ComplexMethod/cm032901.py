def encode_image():
        with BytesIO() as buf:
            img, close_after = open_image_for_processing(d["image"], allow_bytes=False)

            if isinstance(img, bytes):
                buf.write(img)
                buf.seek(0)
                return buf.getvalue()

            if not isinstance(img, Image.Image):
                return None

            if img.mode in ("RGBA", "P"):
                orig_img = img
                img = img.convert("RGB")
                if close_after:
                    try:
                        orig_img.close()
                    except Exception:
                        pass

            try:
                img.save(buf, format="JPEG")
                buf.seek(0)
                return buf.getvalue()
            except OSError as e:
                logging.warning(f"Saving image exception: {e}")
                return None
            finally:
                if close_after:
                    try:
                        img.close()
                    except Exception:
                        pass