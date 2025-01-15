from typing import List, Dict, Optional
import anthropic
from ..models import Interview, Statement
from ..config import ANTHROPIC_API_KEY, AI_MODEL
from datetime import datetime

# Initialize Anthropic client
client = anthropic.Anthropic()

def analyze_interviews(interviews: List[Interview], research_questions: List[str]) -> Dict:
    """Analyze interviews and generate conclusions based on research questions."""
    
    # Prepare all statements for analysis
    all_statements = []
    for interview in interviews:
        all_statements.extend([
            f"{statement.text} (Betrouwbaarheid: {statement.confidence:.2f})"
            for statement in interview.statements
        ])
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8192,
            temperature=0.0,
            system=[
                {
                    "type": "text",
                    "text": """Je bent een expert in het analyseren van interview data en het trekken van diepgaande conclusies.
Je analyseert grondig alle patronen, thema's en verbanden tussen de verschillende statements.
Je onderbouwt al je conclusies met concrete voorbeelden en citaten uit de interviews.
Je structureert je antwoorden zeer duidelijk met:
- Een korte samenvatting aan het begin
- Duidelijke kopjes per onderzoeksvraag
- Subkopjes voor verschillende aspecten
- Concrete voorbeelden en citaten
- Heldere conclusies
- Nuances en kanttekeningen waar nodig
- Aanbevelingen voor vervolgonderzoek

Wees zo uitgebreid als nodig om de vragen goed te beantwoorden."""
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": f"""Analyseer de volgende interview statements en beantwoord de onderzoeksvragen.
Geef een zeer grondige analyse met:

1. Samenvatting
- Korte overview van de belangrijkste bevindingen
- Algemene patronen en thema's
- Belangrijkste conclusies

2. Per onderzoeksvraag:
- Duidelijk antwoord op de vraag
- Uitgebreide onderbouwing met relevante statements
- Analyse van patronen en thema's
- Concrete voorbeelden en citaten
- Nuances en kanttekeningen
- Deelconclusies

3. Overkoepelende conclusies
- Synthese van alle bevindingen
- Belangrijkste inzichten
- Aanbevelingen voor vervolgonderzoek

Onderzoeksvragen:
{chr(10).join(f"- {q}" for q in research_questions)}

Interview Statements:
{chr(10).join(all_statements)}"""
                }
            ]
        )
        
        # Process and structure the response
        analysis_result = {
            'raw_response': response.content[0].text if isinstance(response.content, list) else response.content,
            'questions': research_questions,
            'timestamp': datetime.now().isoformat(),
            'statements_analyzed': len(all_statements),
            'interviews_analyzed': len(interviews),
            'model_used': "claude-3-5-sonnet-20241022"
        }
        
        return analysis_result
    
    except Exception as e:
        print(f"Error in analysis: {str(e)}")
        return None

def search_analysis_statements(interviews: List[Interview], search_query: str) -> List[Statement]:
    """Search through all statements marked for analysis."""
    matching_statements = []
    
    for interview in interviews:
        for statement in interview.statements:
            if search_query.lower() in statement.text.lower():
                matching_statements.append(statement)
    
    return matching_statements 

def chat_with_analysis(
    prompt: str,
    interviews: List[Interview],
    research_questions: List[str],
    chat_history: List[Dict]
) -> Dict:
    """Chat with AI about the analysis, allowing for clarifications and reformatting."""
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # Prepare context
        statements_text = "\n".join([
            f"- {s.text} (Type: {s.type.value}, Confidence: {s.confidence:.2f})"
            for interview in interviews
            for s in interview.statements
        ])
        
        questions_text = "\n".join([f"- {q}" for q in research_questions])
        
        # Prepare chat history
        history_text = "\n".join([
            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
            for msg in chat_history[-5:]  # Only include last 5 messages for context
        ])
        
        # Create system message
        system_message = """Je bent een behulpzame assistent die ondersteuning biedt bij het analyseren van interviews.
Je hebt toegang tot de volgende informatie:

ONDERZOEKSVRAGEN:
{}

STATEMENTS UIT INTERVIEWS:
{}

RECENTE CHAT GESCHIEDENIS:
{}

Je taak is om de gebruiker te helpen met:
1. Het beantwoorden van vragen over de analyse
2. Het herformatteren van de analyse op verzoek
3. Het verduidelijken van conclusies

Belangrijke regels:
- Baseer je conclusies ALLEEN op de gegeven statements
- Wees duidelijk en professioneel
- Als je een nieuwe versie van de analyse maakt, gebruik dan markdown formatting
- Begin elke nieuwe versie van de analyse met de standaard metadata sectie

Als je een nieuwe versie van de analyse maakt, begin dan met '# Interview Analyse Rapport'
Als je alleen een vraag beantwoordt, geef dan een normaal antwoord.""".format(
            questions_text,
            statements_text,
            history_text
        )
        
        # Send message to AI
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8192,
            temperature=0.1,
            system=system_message,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse response
        try:
            # Extract text from response content
            if isinstance(response.content, list):
                response_text = response.content[0].text
            else:
                response_text = response.content
            
            # Check if response contains a new analysis version
            if "# Interview Analyse Rapport" in response_text:
                return {
                    'message': "Ik heb een nieuwe versie van de analyse gemaakt op basis van je verzoek.",
                    'new_analysis': response_text
                }
            else:
                return {
                    'message': response_text
                }
        except Exception as e:
            return {
                'message': f"Er is een fout opgetreden bij het verwerken van het antwoord: {str(e)}"
            }
    
    except Exception as e:
        return {
            'message': f"Er is een fout opgetreden: {str(e)}"
        } 