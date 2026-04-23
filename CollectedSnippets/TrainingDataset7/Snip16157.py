def test_popup_template_escaping(self):
        popup_response_data = json.dumps(
            {
                "new_value": "new_value\\",
                "obj": "obj\\",
                "value": "value\\",
            }
        )
        context = {
            "popup_response_data": popup_response_data,
        }
        output = render_to_string("admin/popup_response.html", context)
        self.assertIn(r"&quot;value\\&quot;", output)
        self.assertIn(r"&quot;new_value\\&quot;", output)
        self.assertIn(r"&quot;obj\\&quot;", output)