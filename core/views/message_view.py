from .json_view import makeJson

def getMessage(**message) -> str:
    """
    Returns a message to the user.
    """
    return makeJson(message)