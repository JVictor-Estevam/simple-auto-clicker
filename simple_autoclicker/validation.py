def is_valid_decimal(value: str) -> bool:
    if value == "":
        return True
    normalized = value.replace(",", ".")
    if normalized.count(".") > 1:
        return False
    stripped = normalized.lstrip("-")
    if not stripped or stripped == ".":
        return normalized in ("-", ".", ",")
    return all(ch == "." or ch.isdigit() for ch in stripped)


def is_valid_unsigned_int(value: str) -> bool:
    return value == "" or value.isdigit()


def is_valid_signed_int(value: str) -> bool:
    if value == "" or value == "-":
        return True
    if value.isdigit():
        return True
    return value.startswith("-") and value[1:].isdigit()
