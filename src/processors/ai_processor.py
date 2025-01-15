from typing import List, Dict
import anthropic
from ..models import Statement, StatementType, Interview
from ..config import ANTHROPIC_API_KEY, AI_MODEL

# Initialize Anthropic client
client = anthropic.Anthropic()

def analyze_text_segment(text: str, interviewee: str) -> List[Statement]:
    """Analyze a segment of text using Claude to extract statements."""
    
    try:
        print(f"\n=== Analyzing text segment for {interviewee} ===")
        print(f"Text length: {len(text)}")
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8192,
            temperature=0.0,  # Zeer lage temperature voor consistente output
            system=[
                {
                    "type": "text",
                    "text": f"""Je bent een expert in het analyseren van interviews.
Je extraheert belangrijke uitspraken en formuleert ze ALTIJD in het exacte format: "{interviewee} [werkwoord] [statement]"
Gebruik altijd de naam '{interviewee}' aan het begin van elke zin.
Begin elke zin met:
- "{interviewee} denkt..." voor meningen en gedachten
- "{interviewee} voelt..." voor emoties en gevoelens
- "{interviewee} doet..." voor acties en handelingen
- "{interviewee} zegt..." voor uitspraken en mededelingen

Zorg dat elke uitspraak op een nieuwe regel begint en gebruik een lege regel tussen uitspraken.

Bepaal voor elke uitspraak een betrouwbaarheidsscore (ZEKERHEID) tussen 0.0 en 1.0:
- 1.0: Directe quotes of expliciete uitspraken
- 0.9: Zeer duidelijke implicaties of herhaalde thema's
- 0.8: Duidelijke interpretaties van de context
- 0.7: Redelijke aannames gebaseerd op meerdere uitspraken
- 0.6: Voorzichtige interpretaties
- 0.5 of lager: Speculatieve of onduidelijke interpretaties

Als je een aanpassing maakt in de analyse, vermeld dan expliciet dat de gebruiker de wijzigingen kan bekijken in de markdown-tab van de applicatie."""
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": f"""Analyseer het volgende interview segment en extraheer belangrijke uitspraken.
Formuleer elke uitspraak in het exacte format: "{interviewee} [werkwoord] [statement]"

Voor elke relevante uitspraak, bepaal het type:
- DENKT: "{interviewee} denkt/vindt/gelooft..." (voor meningen, overtuigingen, gedachten)
- VOELT: "{interviewee} voelt/is/wordt..." (voor emoties, stemmingen, ervaringen)
- DOET: "{interviewee} gaat/maakt/gebruikt..." (voor acties, gedrag, handelingen)
- ZEGT: "{interviewee} zegt/vertelt/geeft aan..." (voor directe uitspraken, verklaringen)

Geef voor elke uitspraak terug:
TYPE: [denkt/voelt/doet/zegt]
TEKST: {interviewee} [werkwoord] [statement]
ZEKERHEID: [0.0-1.0] (hoe zekerder de interpretatie, hoe hoger de score)

Voorbeeld format:
TYPE: zegt
TEKST: {interviewee} zegt verschillende hobby's te hebben
ZEKERHEID: 1.0  # Directe uitspraak

TYPE: denkt
TEKST: {interviewee} vindt zijn hobby's belangrijk
ZEKERHEID: 0.8  # Interpretatie gebaseerd op context

Interview segment met {interviewee}:
{text}"""
                }
            ]
        )
        
        print("\n=== AI Response ===")
        print(response.content[0].text)
        
        # Process the response
        statements = []
        current_statement = {}
        
        for line in response.content[0].text.split('\n'):
            line = line.strip()
            if not line:
                if current_statement:
                    # Create statement object
                    try:
                        statement_type = {
                            'denkt': StatementType.THOUGHT,
                            'voelt': StatementType.FEELING,
                            'doet': StatementType.ACTION,
                            'zegt': StatementType.STATEMENT
                        }[current_statement['type'].lower()]
                        
                        statement = Statement(
                            text=current_statement['text'],
                            type=statement_type,
                            source_text=current_statement.get('text', ''),
                            confidence=float(current_statement.get('confidence', 0.8))
                        )
                        statements.append(statement)
                        print(f"✓ Created statement: {statement.text} (Type: {statement.type.value}, Confidence: {statement.confidence})")
                    except (KeyError, ValueError) as e:
                        print(f"❌ Error creating statement: {str(e)}")
                        print(f"Current statement data: {current_statement}")
                current_statement = {}
                continue
            
            if line.startswith('TYPE:'):
                current_statement['type'] = line.replace('TYPE:', '').strip()
            elif line.startswith('TEKST:'):
                current_statement['text'] = line.replace('TEKST:', '').strip()
            elif line.startswith('ZEKERHEID:'):
                try:
                    current_statement['confidence'] = float(line.replace('ZEKERHEID:', '').strip())
                except ValueError:
                    current_statement['confidence'] = 0.8
        
        # Process the last statement if exists
        if current_statement:
            try:
                statement_type = {
                    'denkt': StatementType.THOUGHT,
                    'voelt': StatementType.FEELING,
                    'doet': StatementType.ACTION,
                    'zegt': StatementType.STATEMENT
                }[current_statement['type'].lower()]
                
                statement = Statement(
                    text=current_statement['text'],
                    type=statement_type,
                    source_text=current_statement.get('text', ''),
                    confidence=float(current_statement.get('confidence', 0.8))
                )
                statements.append(statement)
                print(f"✓ Created final statement: {statement.text} (Type: {statement.type.value}, Confidence: {statement.confidence})")
            except (KeyError, ValueError) as e:
                print(f"❌ Error creating final statement: {str(e)}")
                print(f"Current statement data: {current_statement}")
        
        print(f"\nTotal statements created: {len(statements)}")
        return statements
    
    except Exception as e:
        print(f"❌ Error in analyze_text_segment: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return []

def process_interview_with_ai(text: str, interviewee: str, max_segment_length: int = 2000) -> Interview:
    """Process complete interview using AI analysis."""
    print(f"\n=== Processing interview for {interviewee} ===")
    print(f"Total text length: {len(text)}")
    
    # Create interview object
    interview = Interview(
        interviewee=interviewee,
        date=None,
        raw_text=text
    )
    
    # Split text into manageable segments
    segments = [text[i:i+max_segment_length] for i in range(0, len(text), max_segment_length)]
    print(f"Split into {len(segments)} segments")
    
    # Process each segment
    total_statements = 0
    for i, segment in enumerate(segments, 1):
        print(f"\nProcessing segment {i}/{len(segments)}")
        statements = analyze_text_segment(segment, interviewee)
        total_statements += len(statements)
        for statement in statements:
            interview.add_statement(statement)
    
    print(f"\nTotal statements added to interview: {len(interview.statements)}")
    return interview 