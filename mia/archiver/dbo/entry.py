import msgspec

class Entry(msgspec.Struct):
    original_url: str
    # Where the URL redirects to. Only populated if status_code == 3xx
    redirect_target: str | None
    filepath: str

    mime_type: str
    status_code: int
