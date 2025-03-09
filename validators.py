import re

async def is_valid_israeli_phone(number: str) -> bool:
    """Validate an Israeli phone number."""
    number = number.strip().replace(" ", "")  # Remove spaces

    # Convert +972 format to local 05X format
    if number.startswith("+972"):
        number = "0" + number[4:]

    pattern = r"^05[012345689]\d{7}$"
    return bool(re.match(pattern, number))

async def is_valid_hebrew_name(name: str) -> bool:
    """Check if the name contains only Hebrew letters."""
    pattern = r"^[א-ת\s]+$"
    return bool(re.match(pattern, name)) and is_valid_name_length(name)

async def is_valid_mileage(mileage: str) -> bool:
    """Check if mileage is a valid float with up to 2 decimal places."""
    return bool(re.match(r"^\d+(\.\d{1,2})?$", mileage))

def is_valid_name_length(name: str) -> bool:
    """Check if the name from length greater than 1."""
    return len(name) > 1


