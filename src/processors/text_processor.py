import re
from typing import List, Tuple
from ..models import Statement, StatementType, Interview
from ..config import MINIMUM_STATEMENT_LENGTH, MAXIMUM_STATEMENT_LENGTH

def dutch_sentence_split(text: str) -> List[str]:
    """Split Dutch text into sentences using common Dutch sentence endings."""
    # Replace common abbreviations to prevent false splits
    text = re.sub(r'(Mr\.|Dr\.|Prof\.|etc\.|bijv\.|bv\.|nl\.|d.w.z\.|m.b.t\.|t.o.v\.|m.i\.|z.s.m\.|a.u.b\.|i.v.m\.|o.a\.|e.d\.|c.q\.|m.a.w\.|n.a.v\.|t.a.v\.)', lambda m: m.group().replace('.', '@'), text)
    
    # Split on sentence endings (.!?) followed by capital letters or whitespace + capital letters
    sentences = re.split(r'([.!?])\s+(?=[A-Z])|([.!?])(?=[A-Z])', text)
    
    # Clean and combine the split parts
    result = []
    current = ""
    for part in sentences:
        if part in ['.', '!', '?', None]:
            if current:
                # Restore abbreviation periods and append sentence
                current = current.replace('@', '.').strip()
                if current:
                    result.append(current)
            current = ""
        else:
            current += (part or "")
    
    # Add the last sentence if it exists
    if current:
        current = current.replace('@', '.').strip()
        if current:
            result.append(current)
    
    return [s for s in result if s]

def clean_text(text: str) -> str:
    """Clean and normalize text."""
    # Remove multiple newlines and whitespace
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s.,!?;:\'\"()-]', '', text)
    return text.strip()

def split_into_segments(text: str, max_length: int = 2000) -> List[str]:
    """Split text into manageable segments while preserving sentence boundaries."""
    sentences = dutch_sentence_split(text)
    segments = []
    current_segment = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence)
        if current_length + sentence_length > max_length and current_segment:
            segments.append(' '.join(current_segment))
            current_segment = [sentence]
            current_length = sentence_length
        else:
            current_segment.append(sentence)
            current_length += sentence_length
    
    if current_segment:
        segments.append(' '.join(current_segment))
    
    return segments

def extract_statement_type(text: str) -> Tuple[StatementType, float]:
    """Determine the type of statement and confidence level."""
    text_lower = text.lower()
    
    # Simple rule-based classification
    indicators = {
        StatementType.THOUGHT: ['denk', 'vind', 'meen', 'geloof', 'verwacht'],
        StatementType.FEELING: ['voel', 'bang', 'blij', 'boos', 'verdrietig', 'zorgen'],
        StatementType.ACTION: ['doe', 'maak', 'ga', 'gebruik', 'werk'],
        StatementType.STATEMENT: ['zeg', 'vertel', 'antwoord', 'reageer', 'opmerk']
    }
    
    max_confidence = 0.0
    statement_type = StatementType.STATEMENT  # default
    
    for type_, words in indicators.items():
        confidence = sum(1 for word in words if word in text_lower)
        confidence = min(confidence / len(words), 1.0)
        if confidence > max_confidence:
            max_confidence = confidence
            statement_type = type_
    
    return statement_type, max_confidence

def process_segment(segment: str, interviewee: str) -> List[Statement]:
    """Process a text segment and extract statements."""
    statements = []
    sentences = dutch_sentence_split(segment)
    
    for sentence in sentences:
        if MINIMUM_STATEMENT_LENGTH <= len(sentence) <= MAXIMUM_STATEMENT_LENGTH:
            statement_type, confidence = extract_statement_type(sentence)
            
            # Create statement with proper format
            formatted_text = f"{interviewee} {statement_type.value} {sentence}"
            
            statement = Statement(
                text=formatted_text,
                type=statement_type,
                source_text=sentence,
                confidence=confidence
            )
            statements.append(statement)
    
    return statements

def process_interview(text: str, interviewee: str) -> Interview:
    """Process complete interview text."""
    # Clean the text
    cleaned_text = clean_text(text)
    
    # Create interview object
    interview = Interview(
        interviewee=interviewee,
        date=None,  # Can be set later if date information is available
        raw_text=cleaned_text
    )
    
    # Split into segments and process each
    segments = split_into_segments(cleaned_text)
    for segment in segments:
        statements = process_segment(segment, interviewee)
        for statement in statements:
            interview.add_statement(statement)
    
    return interview 