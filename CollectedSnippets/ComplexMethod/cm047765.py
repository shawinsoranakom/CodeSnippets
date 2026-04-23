def convert_to_pdfa(self):
        """
        Transform the opened PDF file into a PDF/A compliant file
        """
        # Set the PDF version to 1.7 (as PDF/A-3 is based on version 1.7) and make it PDF/A compliant.
        # See https://github.com/veraPDF/veraPDF-validation-profiles/wiki/PDFA-Parts-2-and-3-rules#rule-612-1
        self._header = b"%PDF-1.7"

        # " The file header shall begin at byte zero and shall consist of "%PDF-1.n" followed by a single EOL marker,
        # where 'n' is a single digit number between 0 (30h) and 7 (37h) "
        # " The aforementioned EOL marker shall be immediately followed by a % (25h) character followed by at least four
        # bytes, each of whose encoded byte values shall have a decimal value greater than 127 ".
        # PyPDF2 2.X+ already adds these 4 characters by default (so ._pypdf2_2 and ._pypdf don't need it).
        # The injected character `\xc3\xa9` is equivalent to the character `é`.
        # Therefore, on `_pypdf2_1`, the header will look like: `%PDF-1.7\n%éééé`,
        # while on `_pypdf2_2` and `_pypdf`, it will look like: `%PDF-1.7\n%âãÏÓ`.
        if SUBMOD == '._pypdf2_1':
            self._header += b"\n%\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9"

        # Add a document ID to the trailer. This is only needed when using encryption with regular PDF, but is required
        # when using PDF/A
        pdf_id = ByteStringObject(md5(self._reader.stream.getvalue()).digest())
        # The first string is based on the content at the time of creating the file, while the second is based on the
        # content of the file when it was last updated. When creating a PDF, both are set to the same value.
        self._set_id(ArrayObject((pdf_id, pdf_id)))

        with file_open('tools/data/files/sRGB2014.icc', mode='rb') as icc_profile:
            icc_profile_file_data = compress(icc_profile.read())

        icc_profile_stream_obj = DecodedStreamObject()
        icc_profile_stream_obj.setData(icc_profile_file_data)
        icc_profile_stream_obj.update({
            NameObject("/Filter"): NameObject("/FlateDecode"),
            NameObject("/N"): NumberObject(3),
            NameObject("/Length"): NameObject(str(len(icc_profile_file_data))),
        })

        icc_profile_obj = self._addObject(icc_profile_stream_obj)

        output_intent_dict_obj = DictionaryObject()
        output_intent_dict_obj.update({
            NameObject("/S"): NameObject("/GTS_PDFA1"),
            NameObject("/OutputConditionIdentifier"): createStringObject("sRGB"),
            NameObject("/DestOutputProfile"): icc_profile_obj,
            NameObject("/Type"): NameObject("/OutputIntent"),
        })

        output_intent_obj = self._addObject(output_intent_dict_obj)
        self._root_object.update({
            NameObject("/OutputIntents"): ArrayObject([output_intent_obj]),
        })

        pages = self._root_object['/Pages']['/Kids']

        # PDF/A needs the glyphs width array embedded in the pdf to be consistent with the ones from the font file.
        # But it seems like it is not the case when exporting from wkhtmltopdf.
        try:
            import fontTools.ttLib  # noqa: PLC0415
        except ImportError:
            _logger.warning('The fonttools package is not installed. Generated PDF may not be PDF/A compliant.')
        else:
            fonts = {}
            # First browse through all the pages of the pdf file, to get a reference to all the fonts used in the PDF.
            for page in pages:
                for font in page.getObject()['/Resources']['/Font'].values():
                    for descendant in font.getObject()['/DescendantFonts']:
                        fonts[descendant.idnum] = descendant.getObject()

            # Then for each font, rewrite the width array with the information taken directly from the font file.
            # The new width are calculated such as width = round(1000 * font_glyph_width / font_units_per_em)
            # See: http://martin.hoppenheit.info/blog/2018/pdfa-validation-and-inconsistent-glyph-width-information/
            for font in fonts.values():
                font_file = font['/FontDescriptor']['/FontFile2']
                stream = io.BytesIO(decompress(font_file._data))
                ttfont = fontTools.ttLib.TTFont(stream)
                font_upm = ttfont['head'].unitsPerEm
                if parse_version(fontTools.__version__) < parse_version('4.37.2'):
                    glyphs = ttfont.getGlyphSet()._hmtx.metrics
                else:
                    glyphs = ttfont.getGlyphSet().hMetrics
                glyph_widths = []
                for key, values in glyphs.items():
                    if key[:5] == 'glyph':
                        glyph_widths.append(NumberObject(round(1000.0 * values[0] / font_upm)))

                font[NameObject('/W')] = ArrayObject([NumberObject(1), ArrayObject(glyph_widths)])
                stream.close()

        outlines = self._root_object['/Outlines'].getObject()
        outlines[NameObject('/Count')] = NumberObject(1)

        # [6.7.2.2-1] include a MarkInfo dictionary containing "Marked" with true value
        mark_info = DictionaryObject({NameObject("/Marked"): BooleanObject(True)})
        self._root_object[NameObject("/MarkInfo")] = mark_info

        # [6.7.3.3-1] include minimal document structure in the catalog
        struct_tree_root = DictionaryObject({NameObject("/Type"): NameObject("/StructTreeRoot")})
        self._root_object[NameObject("/StructTreeRoot")] = struct_tree_root

        # Set odoo as producer
        self.addMetadata({
            '/Creator': "Odoo",
            '/Producer': "Odoo",
        })
        self.is_pdfa = True