def __init__(self, message, last_response):
        super().__init__(message)
        self.last_response = last_response
        self.redirect_chain = last_response.redirect_chain