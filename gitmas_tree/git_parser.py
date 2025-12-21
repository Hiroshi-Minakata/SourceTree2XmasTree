import subprocess
from dataclasses import dataclass

@dataclass
class Commit:
    hash: str
    parents: list[str]
    time: int
    message: str
    branch: str

def load_commits(repo_path, depth) -> list[Commit]:
    logs = subprocess.check_output(
        f"git log --all --reverse -n {depth} --pretty=format:%H|%P|%ct|%s|%D",
        cwd=repo_path,
        encoding="utf-8",
        text=True,
    ).splitlines()

    commits = []
    for log in logs:
        parts = log.split("|")
        hash = parts[0]
        parents = parts[1].split() if parts[1] else []
        time = int(parts[2])
        message = parts[3] if len(parts) > 3 else ""
        branch = parts[4] if len(parts) > 4 else ""
        commits.append(Commit(hash, parents, time, message, branch))

    return commits
