def merge_span_token(master_token_list):
    """
    Merge the span style token (row span or col span).
    :param master_token_list:
    :return:
    """
    new_master_token_list = []
    pointer = 0
    if master_token_list[-1] != "</tbody>":
        master_token_list.append("</tbody>")
    while master_token_list[pointer] != "</tbody>":
        try:
            if master_token_list[pointer] == "<td":
                if master_token_list[pointer + 1].startswith(
                    " colspan="
                ) or master_token_list[pointer + 1].startswith(" rowspan="):
                    """
                    example:
                    pattern <td colspan="3">
                    '<td' + 'colspan=" "' + '>' + '</td>'
                    """
                    tmp = "".join(master_token_list[pointer : pointer + 3 + 1])
                    pointer += 4
                    new_master_token_list.append(tmp)

                elif master_token_list[pointer + 2].startswith(
                    " colspan="
                ) or master_token_list[pointer + 2].startswith(" rowspan="):
                    """
                    example:
                    pattern <td rowspan="2" colspan="3">
                    '<td' + 'rowspan=" "' + 'colspan=" "' + '>' + '</td>'
                    """
                    tmp = "".join(master_token_list[pointer : pointer + 4 + 1])
                    pointer += 5
                    new_master_token_list.append(tmp)

                else:
                    new_master_token_list.append(master_token_list[pointer])
                    pointer += 1
            else:
                new_master_token_list.append(master_token_list[pointer])
                pointer += 1
        except:
            print("Break in merge...")
            break
    new_master_token_list.append("</tbody>")

    return new_master_token_list