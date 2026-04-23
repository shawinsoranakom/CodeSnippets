def readSheet(self, sheet):
        name = sheet.getAttribute("name")
        rows = sheet.getElementsByType(TableRow)
        arrRows = []

        # for each row
        for row in rows:
            arrCells = []
            cells = row.getElementsByType(TableCell)

            # for each cell
            for count, cell in enumerate(cells, start=1):
                # repeated value?
                repeat = 0
                if count != len(cells):
                    repeat = cell.getAttribute("numbercolumnsrepeated")
                if not repeat:
                    repeat = 1
                    spanned = int(cell.getAttribute('numbercolumnsspanned') or 0)
                    # clone spanned cells
                    if self.clonespannedcolumns is not None and spanned > 1:
                        repeat = spanned

                ps = cell.getElementsByType(P)
                textContent = u""

                # for each text/text:span node
                for p in ps:
                    for n in p.childNodes:
                        if n.nodeType == 1 and n.tagName == "text:span":
                            for c in n.childNodes:
                                if c.nodeType == 3:
                                    textContent = u'{}{}'.format(textContent, n.data)

                        if n.nodeType == 3:
                            textContent = u'{}{}'.format(textContent, n.data)

                if not textContent.startswith("#"):  # ignore comments cells
                    arrCells.extend([textContent] * int(repeat))

            # if row contained something
            if arrCells:
                arrRows.append(arrCells)

            #else:
            #    print ("Empty or commented row (", row_comment, ")")

        self.SHEETS[name] = arrRows