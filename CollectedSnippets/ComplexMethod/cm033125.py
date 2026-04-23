async def __img_ocr(i, id, img, chars, limiter):
            j = 0
            while j + 1 < len(chars):
                if (
                    chars[j]["text"]
                    and chars[j + 1]["text"]
                    and re.match(r"[0-9a-zA-Z,.:;!%]+", chars[j]["text"] + chars[j + 1]["text"])
                    and chars[j + 1]["x0"] - chars[j]["x1"] >= min(chars[j + 1]["width"], chars[j]["width"]) / 2
                ):
                    chars[j]["text"] += " "
                j += 1

            if limiter:
                async with limiter:
                    await thread_pool_exec(self.__ocr, i + 1, img, chars, zoomin, id)
            else:
                self.__ocr(i + 1, img, chars, zoomin, id)

            if callback and i % 6 == 5:
                callback((i + 1) * 0.6 / len(self.page_images))