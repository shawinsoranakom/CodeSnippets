def get_pred_html_master(self, pred_structures, matched_index, ocr_contents):
        end_html = []
        td_index = 0
        for token in pred_structures:
            if "</td>" in token:
                txt = ""
                b_with = False
                if td_index in matched_index.keys():
                    if (
                        "<b>" in ocr_contents[matched_index[td_index][0]]
                        and len(matched_index[td_index]) > 1
                    ):
                        b_with = True
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
                            if (
                                i != len(matched_index[td_index]) - 1
                                and " " != content[-1]
                            ):
                                content += " "
                        txt += content
                if b_with:
                    txt = "<b>{}</b>".format(txt)
                if "<td></td>" == token:
                    token = "<td>{}</td>".format(txt)
                else:
                    token = "{}</td>".format(txt)
                td_index += 1
            token = deal_eb_token(token)
            end_html.append(token)
        html = "".join(end_html)
        html = deal_bb(html)
        return html, end_html