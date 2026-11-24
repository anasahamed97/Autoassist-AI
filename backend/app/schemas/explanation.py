from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator
from backend.app.schemas.rag import RAGSearchResultItem


class SimpleExplanation(BaseModel):
    what_does_it_mean: str
    why_does_it_happen: str
    symptoms_you_might_notice: List[str]
    what_should_you_do: List[str]
    when_to_visit_mechanic: str
    safety_warnings: List[str]
    suggested_mechanic_questions: List[str]


class DualViewManualResult(BaseModel):
    query: str
    total_matches: int
    latency_ms: float
    # View 1: Technical OEM Passages
    technical_passages: List[RAGSearchResultItem]
    # View 2: Simple Plain-Language Grounded Explanation
    simple_explanation: SimpleExplanation
    questions_for_mechanic: Optional[List[str]] = None
    disclaimer: str = (
        "Grounding notice: Simple explanations are derived from verified technical manual passages and "
        "automotive engineering principles. They are intended for educational clarity and customer empowerment."
    )

    @model_validator(mode="after")
    def populate_mechanic_questions(self) -> "DualViewManualResult":
        if not self.questions_for_mechanic and self.simple_explanation:
            self.questions_for_mechanic = self.simple_explanation.suggested_mechanic_questions
        return self
