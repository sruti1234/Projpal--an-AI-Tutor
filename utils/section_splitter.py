import re

def split_sections(text):
    sections = {}
    headings = [
        'abstract', 'introduction', 'problem statement', 'objective',
        'methodology', 'proposed system', 'implementation',
        'results', 'conclusion', 'future scope'
    ]

    for heading in headings:
        pattern = rf"{heading}[\s\S]*?(?=\n[a-zA-Z ]{{2,40}}\n|\Z)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            sections[heading.title()] = match.group().strip()

    return sections
