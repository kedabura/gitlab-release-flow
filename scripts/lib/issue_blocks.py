import re


def extract_block(text, start_marker, end_marker):
    pattern = re.compile(
        rf"{re.escape(start_marker)}(.*?){re.escape(end_marker)}",
        re.DOTALL,
    )
    match = pattern.search(text or "")
    if not match:
        return None
    return match.group(1)


def replace_block(text, start_marker, end_marker, new_content):
    pattern = re.compile(
        rf"({re.escape(start_marker)})(.*)({re.escape(end_marker)})",
        re.DOTALL,
    )
    return pattern.sub(rf"\1\n{new_content}\n\3", text)