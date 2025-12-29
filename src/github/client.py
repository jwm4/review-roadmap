import httpx
from typing import Optional
from src.config import settings
from src.models import PRContext, PRMetadata, FileDiff

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.GITHUB_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        self.client = httpx.Client(headers=self.headers, base_url="https://api.github.com", follow_redirects=True)

    def get_pr_context(self, owner: str, repo: str, pr_number: int) -> PRContext:
        """Fetches all necessary context for a PR."""
        
        # 1. Fetch PR Metadata
        pr_resp = self.client.get(f"/repos/{owner}/{repo}/pulls/{pr_number}")
        pr_resp.raise_for_status()
        pr_data = pr_resp.json()
        
        metadata = PRMetadata(
            number=pr_data["number"],
            title=pr_data["title"],
            description=pr_data["body"] or "",
            author=pr_data["user"]["login"],
            base_branch=pr_data["base"]["ref"],
            head_branch=pr_data["head"]["ref"],
            head_commit_sha=pr_data["head"]["sha"],
            repo_url=pr_data["head"]["repo"]["html_url"],
            is_draft=pr_data["draft"]
        )

        # 2. Fetch File Diffs
        files_resp = self.client.get(f"/repos/{owner}/{repo}/pulls/{pr_number}/files")
        files_resp.raise_for_status()
        files_data = files_resp.json()
        
        files = []
        for f in files_data:
            files.append(FileDiff(
                path=f["filename"],
                status=f["status"],
                additions=f["additions"],
                deletions=f["deletions"],
                diff_content=f.get("patch", "")  # Patch might be missing for binary/large files
            ))

        return PRContext(metadata=metadata, files=files)
