"""Autonomous Git Branch and Pull Request Dispatcher for Vo-Gen-Flow."""

import os
import re
import subprocess
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger("vogenflow.dispatcher")

DEFAULT_AUTHOR = "maihun-rsc <rananjaychauhan93@gmail.com>"


class PRDispatcher:
    """Automates Git branch creation, atomic file commits, and Pull Request generation."""

    def __init__(self, repo_root: Optional[str] = None, author: str = DEFAULT_AUTHOR):
        if repo_root is None:
            # Default to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            repo_root = base_dir
        self.repo_root = repo_root
        self.author = author

    def _run_git(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command in the repository root."""
        cmd = ["git"] + args
        try:
            return subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=check
            )
        except Exception as e:
            logger.warning("Git command failed %s: %s", cmd, str(e))
            raise

    def get_current_branch(self) -> str:
        """Return the active Git branch name."""
        try:
            res = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
            return res.stdout.strip()
        except Exception:
            return "main"

    def create_feature_branch(self, branch_name: str) -> Dict[str, Any]:
        """Create and checkout a new feature branch."""
        # Sanitize branch name
        clean_name = re.sub(r"[^a-zA-Z0-9_\-\/]", "-", branch_name).strip("-")
        try:
            self._run_git(["checkout", "-b", clean_name])
            logger.info("Created and checked out branch: %s", clean_name)
            return {"status": "success", "branch": clean_name}
        except Exception as e:
            logger.error("Failed to create branch %s: %s", clean_name, str(e))
            return {"status": "error", "branch": clean_name, "error": str(e)}

    def commit_files(self, file_paths: List[str], commit_message: str) -> Dict[str, Any]:
        """Stage specified files and commit with the verified author."""
        try:
            for path in file_paths:
                self._run_git(["add", path])

            commit_args = ["commit", "-m", commit_message, f"--author={self.author}"]
            res = self._run_git(commit_args)
            logger.info("Committed %d files: %s", len(file_paths), commit_message)
            return {
                "status": "success",
                "message": commit_message,
                "author": self.author,
                "output": res.stdout.strip()
            }
        except subprocess.CalledProcessError as cpe:
            # Check if working tree clean / nothing to commit
            if "nothing to commit" in (cpe.stdout + cpe.stderr):
                return {"status": "noop", "message": "Nothing to commit, working tree clean."}
            return {"status": "error", "error": cpe.stderr.strip()}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def dispatch_pr(
        self,
        title: str,
        body: str,
        base_branch: str = "main",
        head_branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """Dispatch a Pull Request via GitHub CLI or construct a ready-to-push PR payload."""
        head = head_branch or self.get_current_branch()

        # Check if GitHub CLI 'gh' is available
        gh_available = False
        try:
            chk = subprocess.run(["gh", "--version"], capture_output=True, text=True)
            gh_available = (chk.returncode == 0)
        except Exception:
            gh_available = False

        if gh_available:
            try:
                cmd = ["gh", "pr", "create", "--title", title, "--body", body, "--base", base_branch, "--head", head]
                res = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True, check=True)
                pr_url = res.stdout.strip()
                logger.info("GitHub PR created successfully: %s", pr_url)
                return {
                    "status": "dispatched",
                    "method": "gh_cli",
                    "pr_url": pr_url,
                    "title": title,
                    "head": head,
                    "base": base_branch
                }
            except Exception as e:
                logger.warning("gh CLI PR creation failed: %s. Falling back to local dispatch payload.", str(e))

        # Dry-run / Local PR Preparation
        return {
            "status": "prepared",
            "method": "local_git",
            "title": title,
            "head": head,
            "base": base_branch,
            "body": body,
            "instructions": f"Push with: git push origin {head} && open PR against {base_branch}"
        }

    def rollback(self, branch_to_delete: str, fallback_branch: str = "main") -> bool:
        """Switch back to fallback branch and delete the feature branch."""
        try:
            self._run_git(["checkout", fallback_branch])
            self._run_git(["branch", "-D", branch_to_delete])
            logger.info("Rolled back cleanly to %s and deleted %s", fallback_branch, branch_to_delete)
            return True
        except Exception as e:
            logger.warning("Rollback error: %s", str(e))
            return False
