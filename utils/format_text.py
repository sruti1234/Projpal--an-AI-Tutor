import re

def format_section_text(text):
    # Split on sentence endings
    sentences = re.split(r'(?<=[.!?]) +', text.strip())
    
    # Build proper HTML list
    bullet_points = ['<li>' + sentence.strip() + '</li>' for sentence in sentences if sentence.strip()]
    
    return '<ul>' + '\n'.join(bullet_points) + '</ul>'
