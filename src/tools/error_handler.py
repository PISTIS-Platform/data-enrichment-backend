class CustomError(Exception):
    def __init__(self, message, origin, status_code, content=None):
        self.message = message
        self.origin = origin
        self.status_code = status_code
        self.content = content
        super().__init__(self.message)


