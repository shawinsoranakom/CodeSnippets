def _add_pages_to_writer(self, writer, document, prefix=None):
        """Add a PDF doc to the writer and fill the form text fields present in the pages if needed.

        :param PdfFileWriter writer: the writer to which pages needs to be added
        :param bytes document: the document to add in the final pdf
        :param str prefix: the prefix needed to update existing form field name, if any, to be able
                           to add the correct values in fields with the same name but on different
                           documents, either customizable fields or dynamic fields of different sale
                           order lines. (optional)
        :return: None
        """
        reader = PdfFileReader(io.BytesIO(document), strict=False)

        field_names = set()
        if prefix:
            field_names = reader.getFormTextFields()

        for page_id in range(reader.getNumPages()):
            page = reader.getPage(page_id)
            if prefix and page.get('/Annots'):
                # Modifying the annots that hold every information about the form fields
                for j in range(len(page['/Annots'])):
                    reader_annot = page['/Annots'][j].getObject()
                    # Check parent object for '/T' if missing.
                    if '/T' not in reader_annot and '/Parent' in reader_annot:
                        reader_annot = reader_annot['/Parent'].getObject()
                    if reader_annot.get('/T') in field_names:
                        # Prefix all form fields in the document with the document identifier.
                        # This is necessary to know which value needs to be taken when filling the forms.
                        form_key = reader_annot.get('/T')
                        new_key = prefix + form_key

                        # Modifying the form flags to force some characteristics
                        # 1. make all text fields read-only
                        # 2. make all text fields support multiline
                        form_flags = reader_annot.get('/Ff', 0)
                        readonly_flag = 1  # 1st bit sets readonly
                        multiline_flag = 1 << 12  # 13th bit sets multiline text
                        new_flags = form_flags | readonly_flag | multiline_flag

                        reader_annot.update({
                            NameObject("/T"): createStringObject(new_key),
                            NameObject("/Ff"): NumberObject(new_flags),
                        })
            writer.addPage(page)