def fill_form_fields_pdf(writer, form_fields):
    ''' Fill in the form fields of a PDF
    :param writer: a PdfFileWriter object
    :param dict form_fields: a dictionary of form fields to update in the PDF
    :return: a filled PDF datastring
    '''

    pypdf_version = parse_version(pypdf.__version__)

    # This solves a known problem with PyPDF2, where with some pdf software, forms fields aren't
    # correctly filled until the user click on it, see: https://github.com/py-pdf/pypdf/issues/355
    if hasattr(writer, 'set_need_appearances_writer'):
        writer.set_need_appearances_writer()
    else:  # This method was renamed in PyPDF2 2.0
        catalog = writer._root_object
        # get the AcroForm tree
        if "/AcroForm" not in catalog:
            writer._root_object.update({
                NameObject("/AcroForm"): IndirectObject(len(writer._objects), 0, writer)
            })
        writer._root_object["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)

    if pypdf_version >= parse_version('3.13.0'):
        catalog = writer._root_object
        if "/Fields" not in catalog.get('/AcroForm'):
            catalog.update({
                NameObject("/AcroForm"): writer._add_object(
                    DictionaryObject({
                        NameObject("/Fields"): ArrayObject()
                    })
                )
            })

    nbr_pages = len(writer.pages) if pypdf_version >= parse_version('1.28.0') else writer.getNumPages()

    for page_id in range(0, nbr_pages):
        page = writer.getPage(page_id)

        if pypdf_version >= parse_version('2.11.0'):
            writer.update_page_form_field_values(page, form_fields)
        else:
            # Known bug on previous versions of PyPDF2, fixed in 2.11
            if not page.get('/Annots'):
                _logger.info("No fields to update in this page")
            else:
                try:
                    writer.updatePageFormFieldValues(page, form_fields)
                except ValueError:
                    # Known bug on previous versions of PyPDF2 for some PDFs, fixed in 2.4.2
                    _logger.info("Fields couldn't be filled in this page.")
                    continue