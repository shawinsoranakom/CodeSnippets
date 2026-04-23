def __images__(self, fnm, zoomin=3, page_from=0, page_to=299, callback=None):
        self.lefted_chars = []
        self.mean_height = []
        self.mean_width = []
        self.boxes = []
        self.garbages = {}
        self.page_cum_height = [0]
        self.page_layout = []
        self.page_from = page_from
        start = timer()
        try:
            with sys.modules[LOCK_KEY_pdfplumber]:
                with pdfplumber.open(fnm) if isinstance(fnm, str) else pdfplumber.open(BytesIO(fnm)) as pdf:
                    self.pdf = pdf
                    self.page_images = [p.to_image(resolution=72 * zoomin, antialias=True).annotated for i, p in enumerate(self.pdf.pages[page_from:page_to])]

                    try:
                        self.page_chars = [[c for c in page.dedupe_chars().chars if self._has_color(c)] for page in self.pdf.pages[page_from:page_to]]
                    except Exception as e:
                        logging.warning(f"Failed to extract characters for pages {page_from}-{page_to}: {str(e)}")
                        self.page_chars = [[] for _ in range(page_to - page_from)]  # If failed to extract, using empty list instead.

                    # Detect garbled pages and clear their chars so the OCR
                    # path will be used instead. Two detection strategies:
                    # 1) PUA / unmapped CID characters (threshold=0.3)
                    # 2) Font-encoding garbling: subset fonts mapping CJK to ASCII
                    for pi, page_ch in enumerate(self.page_chars):
                        if not page_ch:
                            continue
                        # Strategy 1: PUA / CID garbling
                        sample = page_ch if len(page_ch) <= 200 else page_ch[:200]
                        sample_text = "".join(c.get("text", "") for c in sample)
                        if self._is_garbled_text(sample_text, threshold=0.3):
                            logging.warning(
                                "Page %d: pdfplumber extracted mostly garbled characters (%d chars), "
                                "clearing to use OCR fallback.",
                                page_from + pi + 1, len(page_ch),
                            )
                            self.page_chars[pi] = []
                            continue
                        # Strategy 2: font-encoding garbling (CJK mapped to ASCII)
                        if self._is_garbled_by_font_encoding(page_ch):
                            logging.warning(
                                "Page %d: detected font-encoding garbled text "
                                "(subset fonts with no CJK output, %d chars), "
                                "clearing to use OCR fallback.",
                                page_from + pi + 1, len(page_ch),
                            )
                            self.page_chars[pi] = []

                    self.total_page = len(self.pdf.pages)

        except Exception as e:
            logging.exception(f"RAGFlowPdfParser __images__, exception: {e}")
        logging.info(f"__images__ dedupe_chars cost {timer() - start}s")

        logging.debug("Images converted.")
        self.is_english = [
            re.search(r"[ a-zA-Z0-9,/¸;:'\[\]\(\)!@#$%^&*\"?<>._-]{30,}", "".join(random.choices([c["text"] for c in self.page_chars[i]], k=min(100, len(self.page_chars[i])))))
            for i in range(len(self.page_chars))
        ]
        if sum([1 if e else 0 for e in self.is_english]) > len(self.page_images) / 2:
            self.is_english = True
        else:
            self.is_english = False

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

        async def __img_ocr_launcher():
            def __ocr_preprocess():
                chars = self.page_chars[i] if not self.is_english else []
                self.mean_height.append(np.median(sorted([c["height"] for c in chars])) if chars else 0)
                self.mean_width.append(np.median(sorted([c["width"] for c in chars])) if chars else 8)
                self.page_cum_height.append(img.size[1] / zoomin)
                return chars

            if self.parallel_limiter:
                tasks = []

                for i, img in enumerate(self.page_images):
                    chars = __ocr_preprocess()

                    semaphore = self.parallel_limiter[i % settings.PARALLEL_DEVICES]

                    async def wrapper(i=i, img=img, chars=chars, semaphore=semaphore):
                        await __img_ocr(
                            i,
                            i % settings.PARALLEL_DEVICES,
                            img,
                            chars,
                            semaphore,
                        )

                    tasks.append(asyncio.create_task(wrapper()))
                    await asyncio.sleep(0)

                try:
                    await asyncio.gather(*tasks, return_exceptions=False)
                except Exception as e:
                    logging.error(f"Error in OCR: {e}")
                    for t in tasks:
                        t.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)
                    raise

            else:
                for i, img in enumerate(self.page_images):
                    chars = __ocr_preprocess()
                    await __img_ocr(i, 0, img, chars, None)

        start = timer()

        asyncio.run(__img_ocr_launcher())

        logging.info(f"__images__ {len(self.page_images)} pages cost {timer() - start}s")

        if not self.is_english and not any([c for c in self.page_chars]) and self.boxes:
            bxes = [b for bxs in self.boxes for b in bxs]
            self.is_english = re.search(r"[ \na-zA-Z0-9,/¸;:'\[\]\(\)!@#$%^&*\"?<>._-]{30,}", "".join([b["text"] for b in random.choices(bxes, k=min(30, len(bxes)))]))

        logging.debug(f"Is it English: {self.is_english}")

        self.page_cum_height = np.cumsum(self.page_cum_height)
        assert len(self.page_cum_height) == len(self.page_images) + 1
        if len(self.boxes) == 0 and zoomin < 9:
            self.__images__(fnm, zoomin * 3, page_from, page_to, callback)