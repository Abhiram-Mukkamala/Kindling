from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator

class Draft(BaseModel):
    id: str = Field(description="Unique issue identifier slug, e.g. 'd1', 'd2'")
    title: str = Field(description="Action-oriented issue title, under 80 characters")
    context: str = Field(description="Context explaining why the change matters and where to look (2-4 sentences)")
    files_to_touch: List[str] = Field(default_factory=list, description="List of actual source file paths from the repository tree")
    new_files: List[str] = Field(default_factory=list, description="Optional list of new files to create")
    acceptance_criteria: List[str] = Field(default_factory=list, description="3 to 5 concrete, testable checks")
    difficulty: Literal["beginner", "intermediate"] = Field(description="Skill level required for contributors")
    source: Literal["todo", "open_issue", "readme_gap", "screenshot"] = Field(description="Origin signal for this issue")

class DraftList(BaseModel):
    drafts: List[Draft] = Field(default_factory=list, description="List of generated issue drafts (max 3)")

    @field_validator("drafts", mode="after")
    @classmethod
    def cap_to_three(cls, v: List[Draft]) -> List[Draft]:
        return v[:3]

class CodeFinding(BaseModel):
    file_path: str = Field(description="Exact repository path where the finding was identified")
    line_range: Optional[str] = Field(default=None, description="Line number or range (e.g. '14-25' or '42')")
    severity: Literal["low", "medium", "high"] = Field(description="Severity level of the code issue")
    explanation: str = Field(description="Clear explanation of the bug, edge case, or anti-pattern")
    evidence: str = Field(description="Direct quote or snippet from source code demonstrating the finding")
    title: Optional[str] = Field(default=None, description="Optional concise finding title")
    suggested_fix: Optional[str] = Field(default=None, description="Optional suggested resolution")

class CodeAnalysisResult(BaseModel):
    findings: List[CodeFinding] = Field(default_factory=list, description="List of source code analysis findings")

class JudgeResult(BaseModel):
    score: int = Field(ge=1, le=10, description="Quality score between 1 and 10")
    critique: str = Field(description="2 to 3 sentences naming the biggest weaknesses or praise")
    problems: List[str] = Field(default_factory=list, description="Short list of identified problems")

class IssueResult(BaseModel):
    id: str
    original: Draft
    judge: Optional[JudgeResult] = None
    final: Optional[Draft] = None
    models_used: Dict[str, str] = Field(default_factory=dict)
    posted_url: Optional[str] = None

class RunResult(BaseModel):
    repo: str
    issues: List[IssueResult] = Field(default_factory=list)
    code_findings: List[CodeFinding] = Field(default_factory=list)

class PipelineEvent(BaseModel):
    run_id: str
    seq: int = 0
    step: str
    role: str
    model: str
    status: Literal["waiting", "running", "done", "error", "skipped"]
    started_at: str
    duration_ms: Optional[int] = None
    detail: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

# Aliases for backwards compatibility
IssueDraft = Draft
DraftsBatch = DraftList
JudgeCritique = JudgeResult
IssueCard = IssueResult
