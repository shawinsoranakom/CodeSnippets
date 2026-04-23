def test_csp_nonce_in_template(self):
        response = self.client.get("/csp_nonce/")
        nonce = response.context["csp_nonce"]
        self.assertIn(f'<script nonce="{nonce}">', response.text)