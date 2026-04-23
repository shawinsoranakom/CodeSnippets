def get_pred_html(self, pred_structures, matched_index, ocr_contents):
        end_html = []
        td_index = 0
        for tag in pred_structures:
            if "</td>" not in tag:
                end_html.append(tag)
                continue

            if "<td></td>" == tag:
                end_html.extend("<td>")

            if td_index in matched_index.keys():
                b_with = False
                if (
                    "<b>" in ocr_contents[matched_index[td_index][0]]
                    and len(matched_index[td_index]) > 1
                ):
                    b_with = True
                    end_html.extend("<b>")

                for i, td_index_index in enumerate(matched_index[td_index]):
                    content = ocr_contents[td_index_index][0]
                    if len(matched_index[td_index]) > 1:
                        if len(content) == 0:
                            continue

                        if content[0] == " ":
                            content = content[1:]

                        if "<b>" in content:
                            content = content[3:]

                        if "</b>" in content:
                            content = content[:-4]

                        if len(content) == 0:
                            continue

                        if i != len(matched_index[td_index]) - 1 and " " != content[-1]:
                            content += " "
                    end_html.extend(content)

                if b_with:
                    end_html.extend("</b>")

            if "<td></td>" == tag:
                end_html.append("</td>")
            else:
                end_html.append(tag)

            td_index += 1

        # Filter <thead></thead><tbody></tbody> elements
        filter_elements = ["<thead>", "</thead>", "<tbody>", "</tbody>"]
        end_html = [v for v in end_html if v not in filter_elements]
        return "".join(end_html), end_html