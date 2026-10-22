from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

class IssueDraft(BaseModel):
    id: str = Field(description="Unique issue identifier slug, e.g. issue-fix-null-pointer")
    title: str = Field(description="Concise, actionable issue title")
    context: str = Field(description="Background problem explanation and reason for change")
    files_to_touch: List[str] = Field(default_factory=list, description="List of source file paths that need modification")
    acceptance_criteria: List[str] = Field(default_factory=list, description="Clear criteria for when this issue is resolved")
    difficulty: Literal["beginner", "intermediate"] = Field(description="Skill level required for contributors")
    source: Literal["todo", "open_issue", "readme_gap", "screenshot"] = Field(description="Origin signal for this issue")

class DraftsBatch(BaseModel):
    drafts: List[IssueDraft] = Field(default_factory=list, description="List of generated issue drafts (max 3)")

class JudgeCritique(BaseModel):
    score: int = Field(ge=1, le=10, description="Quality score between 1 and 10")
    critique: str = Field(description="2-3 line concise critique highlighting gaps or improvements")

class IssueCard(BaseModel):
    id: str
    original: IssueDraft
    judge: Optional[JudgeCritique] = None
    final: Optional[IssueDraft] = None
    models_used: Dict[str, str] = Field(default_factory=dict)
    posted_url: Optional[str] = None

class PipelineEvent(BaseModel):
    run_id: str
    step: str
    role: str
    model: str
    status: Literal["waiting", "running", "done", "failed"]
    started_at: float
    duration_ms: Optional[int] = None
    payload: Optional[Dict[str, Any]] = None
