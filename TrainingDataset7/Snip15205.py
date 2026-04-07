def find_result_row_texts():
            table = self.selenium.find_element(By.ID, "result_list")
            # Drop header from the result list
            return [row.text for row in table.find_elements(By.TAG_NAME, "tr")][1:]