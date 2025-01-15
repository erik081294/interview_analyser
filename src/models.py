from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum

class StatementType(Enum):
    THOUGHT = "denkt"
    FEELING = "voelt"
    ACTION = "doet"
    STATEMENT = "zegt"

@dataclass
class Statement:
    text: str
    type: StatementType
    source_text: str
    confidence: float
    metadata: Dict = field(default_factory=dict)

@dataclass
class Interview:
    interviewee: str
    date: datetime
    raw_text: str
    statements: List[Statement] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def __init__(self, interviewee: str, date: Optional[datetime] = None, raw_text: str = "", statements: List[Statement] = None, metadata: Dict = None):
        self.interviewee = interviewee
        self.date = date or datetime.now()
        self.raw_text = raw_text
        self.statements = statements or []
        self.metadata = metadata or {}
    
    def add_statement(self, statement: Statement):
        """Add a statement to the interview."""
        if not hasattr(self, 'statements'):
            self.statements = []
        self.statements.append(statement)
    
    def __str__(self):
        return f"Interview with {self.interviewee} on {self.date}"
    
    def get_statements_by_type(self, type: StatementType) -> List[Statement]:
        return [s for s in self.statements if s.type == type]

@dataclass
class Analysis:
    interviews: List[Interview]
    themes: List[str] = field(default_factory=list)
    patterns: Dict = field(default_factory=dict)
    sentiment_scores: Dict = field(default_factory=dict)
    conclusions: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

@dataclass
class AnalysisRequest:
    interviews: List[Interview]
    research_questions: List[str]
    focus_areas: Optional[List[str]] = None
    analysis_types: List[str] = field(default_factory=lambda: ["themes", "patterns", "sentiment"])
    
@dataclass
class AnalysisResult:
    request: AnalysisRequest
    analysis: Analysis
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "completed"
    error: Optional[str] = None 