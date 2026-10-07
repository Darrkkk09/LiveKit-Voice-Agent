import pytest
from phone_parser import parse_phone_number, detect_language, handle_self_corrections

def test_detect_language():
    assert detect_language("My number is 9876543210") == "en"
    assert detect_language("Mera number hai nau aath saat") == "hi"
    assert detect_language("nine eight saat aath 9876543210") == "mixed"
    assert detect_language("मेरा नंबर ९८७६५४३२१० है") == "hi"

def test_handle_self_corrections():
    assert handle_self_corrections("My number is 987 wait 9876543210") == "9876543210"
    assert handle_self_corrections("nine eight galat nine eight seven six five four three two one zero") == "nine eight seven six five four three two one zero"
    assert handle_self_corrections("98765 phir se 9876543210") == "9876543210"
    assert handle_self_corrections("sorry 9876543210") == "9876543210"
    assert handle_self_corrections("9876543210") == "9876543210"

def test_english_parsing():
    num, lang, raw = parse_phone_number("nine eight seven six five four three two one zero")
    assert num == "9876543210"
    assert lang == "en"

    num, lang, raw = parse_phone_number("98765 43210")
    assert num == "9876543210"

    num, lang, raw = parse_phone_number("nine oh seven six five four three two one zero")
    assert num == "9076543210"

def test_hindi_and_devanagari_parsing():
    num, lang, raw = parse_phone_number("nau aath saat chhe paanch chaar teen do ek shunya")
    assert num == "9876543210"
    assert lang == "hi"

    num, lang, raw = parse_phone_number("९८७६५४३२१०")
    assert num == "9876543210"
    assert lang == "hi"

    num, lang, raw = parse_phone_number("sifar ek do teen chaar paanch chhe saat aath nau")
    # Starts with 0, so not valid Indian mobile number starting with 6-9
    assert num is None

def test_multipliers():
    # 9 digits -> should be rejected (return None)
    num, lang, raw = parse_phone_number("nine double seven six five triple nine zero")
    assert num is None

    num, lang, raw = parse_phone_number("nine double seven six five triple nine zero one")
    assert num == "9776599901"

    num, lang, raw = parse_phone_number("nau do aath saat chhe paanch chaar teen do ek")
    assert num == "9887654321"

def test_self_correction_in_parse():
    num, lang, raw = parse_phone_number("My number is 12345 wait 9876543210")
    assert num == "9876543210"

    num, lang, raw = parse_phone_number("Mera number hai 987 galat 9876543210")
    assert num == "9876543210"

def test_grouped_numbers():
    num, lang, raw = parse_phone_number("98 76 54 32 10")
    assert num == "9876543210"

    num, lang, raw = parse_phone_number("987 654 3210")
    assert num == "9876543210"

def test_invalid_format_rejections():
    # Less than 10 digits
    assert parse_phone_number("987654321")[0] is None
    # More than 10 digits
    assert parse_phone_number("98765432100")[0] is None
    # Doesn't start with 6, 7, 8, or 9
    assert parse_phone_number("5876543210")[0] is None
    # Non-digit text only
    assert parse_phone_number("hello world")[0] is None

def test_hybrid_parsing():
    num, lang, raw = parse_phone_number("Mera number hai ki 9 8 7 6 5 4 3 2 1 0")
    assert num == "9876543210"
    assert lang == "hi" or lang == "mixed"

    num, lang, raw = parse_phone_number("Mera number hai 9 8 7 6 5 4 3 2 1 0")
    assert num == "9876543210"
    assert lang == "hi" or lang == "mixed"

