import re

def compute_cc_density(text: str) -> float:
    conjunct_pattern = re.compile(r'[\u0995-\u09B9]\u09CD[\u0995-\u09B9]')
    matches = conjunct_pattern.findall(text)
    cc_count = len(matches)
    char_count = max(len(text), 1)
    return round((cc_count / char_count) * 100, 2)