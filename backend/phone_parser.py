import re
from typing import Tuple, Optional

# Mapping of English word digits to numeric strings
ENGLISH_DIGITS = {
    "zero": "0", "oh": "0", "one": "1", "two": "2", "three": "3",
    "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9"
}

# Mapping of Hindi/Hinglish word digits (transliterated and Devanagari) to numeric strings
HINDI_DIGITS = {
    "shunya": "0", "sifar": "0", "ek": "1", "do": "2", "teen": "3",
    "chaar": "4", "char": "4", "paanch": "5", "panch": "5", "chhe": "6",
    "che": "6", "saat": "7", "sat": "7", "aath": "8", "ath": "8",
    "nau": "9", "noo": "9",
    "शून्य": "0", "सिफर": "0", "एक": "1", "दो": "2", "तीन": "3",
    "चार": "4", "पांच": "5", "पाँच": "5", "छह": "6", "छः": "6", "छे": "6",
    "सात": "7", "आठ": "8", "नौ": "9"
}

# Mapping of Devanagari digit characters to numeric strings
DEVANAGARI_DIGITS = {
    "०": "0", "१": "1", "२": "2", "३": "3", "४": "4",
    "५": "5", "६": "6", "७": "7", "८": "8", "९": "9"
}

# Multiplier mappings for repeated numbers
MULTIPLIERS = {
    "double": 2,
    "triple": 3,
    "do": 2
}

# Words indicating a self-correction in spoken transcript
CORRECTION_WORDS = ["wait", "sorry", "galat", "no", "phir se", "phirse", "correction", "wrong"]

# Helper to split text into words while keeping Devanagari Unicode words intact
def _tokenize(text: str):
    return [t.strip(',.!?') for t in text.split() if t.strip(',.!?')]

# Expanded vocabulary set for Hindi and Hinglish speech detection
HINDI_VOCAB = {
    "shunya", "sifar", "ek", "do", "teen", "chaar", "char", "paanch", "panch", "chhe",
    "che", "saat", "sat", "aath", "ath", "nau", "noo",
    "mera", "meri", "mere", "hai", "hain", "ho", "hu", "hoon", "ka", "ki", "ke", "ko",
    "se", "par", "apna", "apni", "aapka", "aapki", "haan", "sahi", "thik", "theek",
    "ji", "na", "nahi", "galat", "phir", "phirse", "koshish", "bataiye", "suno", "sun",
    "batao", "bata", "kripya"
}

# Identify language based on vocabulary presence in transcript
def detect_language(transcript: str) -> str:
    words = [w.lower() for w in _tokenize(transcript)]
    has_en = False
    has_hi = False
    
    if re.search(r'[\u0900-\u097F]', transcript):
        has_hi = True
        
    for w in words:
        if w in ENGLISH_DIGITS or w in ["double", "triple"]:
            has_en = True
        if w in HINDI_DIGITS or w in HINDI_VOCAB:
            has_hi = True

    if has_en and has_hi:
        return "mixed"
    elif has_hi:
        return "hi"
    else:
        return "en"

# Remove speech prior to the last self-correction keyword
def handle_self_corrections(transcript: str) -> str:
    lowered = transcript.lower()
    last_idx = -1
    
    for word in CORRECTION_WORDS:
        pattern = r'\b' + re.escape(word) + r'\b'
        matches = [m.start() for m in re.finditer(pattern, lowered)]
        if matches:
            last_idx = max(last_idx, max(matches))
            
    if last_idx != -1:
        matched_str = lowered[last_idx:]
        for word in CORRECTION_WORDS:
            pattern = r'^\b' + re.escape(word) + r'\b'
            m = re.match(pattern, matched_str)
            if m:
                return transcript[last_idx + m.end():].strip()
        words_after = transcript[last_idx:].split(maxsplit=1)
        return words_after[1] if len(words_after) > 1 else ""
        
    return transcript

# Helper to normalize word token to single digit character if matching any dictionary
def _normalize_digit_token(token: str) -> Optional[str]:
    tok = token.lower().strip(',.!?')
    if tok in ENGLISH_DIGITS:
        return ENGLISH_DIGITS[tok]
    if tok in HINDI_DIGITS:
        return HINDI_DIGITS[tok]
    if tok in DEVANAGARI_DIGITS:
        return DEVANAGARI_DIGITS[tok]
    if tok.isdigit():
        return tok
    return None

# Extract all numeric digit characters from transcript using word mappings & multipliers
def extract_digits(raw_transcript: str) -> str:
    if not raw_transcript or not raw_transcript.strip():
        return ""
        
    cleaned_transcript = handle_self_corrections(raw_transcript)
    
    text = cleaned_transcript
    for dev_char, ascii_digit in DEVANAGARI_DIGITS.items():
        text = text.replace(dev_char, f" {ascii_digit} ")

    tokens = _tokenize(text)
    
    parsed_digits = []
    i = 0
    n = len(tokens)
    
    while i < n:
        token = tokens[i]
        tok_lower = token.lower()
        
        if tok_lower in ["double", "triple"]:
            multiplier = 2 if tok_lower == "double" else 3
            if i + 1 < n:
                next_digit = _normalize_digit_token(tokens[i + 1])
                if next_digit:
                    parsed_digits.append(next_digit * multiplier)
                    i += 2
                    continue
        elif tok_lower == "do" and i + 1 < n:
            next_digit = _normalize_digit_token(tokens[i + 1])
            prev_is_digit = (i > 0 and _normalize_digit_token(tokens[i-1]) is not None)
            if next_digit and not (prev_is_digit and next_digit == "1"):
                parsed_digits.append(next_digit * 2)
                i += 2
                continue
                    
        digit = _normalize_digit_token(tok_lower)
        if digit:
            parsed_digits.append(digit)
        elif token.isdigit():
            parsed_digits.append(token)
            
        i += 1
        
    return "".join(parsed_digits)

# Parse transcript to extract structured 10-digit Indian mobile number
def parse_phone_number(raw_transcript: str) -> Tuple[Optional[str], str, str]:
    if not raw_transcript or not raw_transcript.strip():
        return None, "en", raw_transcript

    detected_lang = detect_language(raw_transcript)
    combined_digits = extract_digits(raw_transcript)
    
    # Validate against Indian mobile number regex: exactly 10 digits starting with 6, 7, 8, or 9
    if re.match(r'^[6-9]\d{9}$', combined_digits):
        return combined_digits, detected_lang, raw_transcript
        
    return None, detected_lang, raw_transcript
