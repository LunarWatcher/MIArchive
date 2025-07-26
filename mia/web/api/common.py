import msgspec

class MessageResponse(msgspec.Struct):
    message: str
