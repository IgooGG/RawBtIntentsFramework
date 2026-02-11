# RawBtIntents.py
from urllib.parse import quote

RAWBT_PACKAGE = "ru.a402d.rawbtprinter"
RAWBT_SCHEME = "rawbt"


def build_intent_uri(text: str) -> str:
    if text is None:
        text = ""
    payload = quote(text, safe="")  # supports \n -> %0A
    return f"intent:{payload}#Intent;scheme={RAWBT_SCHEME};package={RAWBT_PACKAGE};end"


def print_text(text: str) -> str:
    return build_intent_uri(text)
