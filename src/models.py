from typing import List, Optional
from pydantic import BaseModel, Field

class FileDiff(BaseModel):
    path: str
    status: str  # added, modified, removed, renamed
    additions: int
    deletions: int
    diff_content: str = Field(description="The actual unified diff content for this file")
    
    def get_github_link(self, repo_url: str, commit_sha: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
        """Generates a deep link to the file at a specific commit."""
        base = f"{repo_url}/blob/{commit_sha}/{self.path}"
        if start_line and end_line:
            return f"{base}#L{start_line}-L{end_line}"
        if start_line:
            return f"{base}#L{start_line}"
        return base

class PRMetadata(BaseModel):
    number: int
    title: str
    description: str
    author: str
    base_branch: str
    head_branch: str
    head_commit_sha: str
    repo_url: str
    is_draft: bool

class PRContext(BaseModel):
    metadata: PRMetadata
    files: List[FileDiff]
    comments: List[str] = Field(default_factory=list)
