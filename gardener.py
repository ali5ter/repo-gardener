#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @file: gardener.py
# @brief: Enforce GitHub repo state from repos.yaml
# @author: Alister Lewis-Bowen <alister@lewis-bowen.org>

import subprocess
import yaml
import sys
import json
import re
from subprocess import CalledProcessError
from pathlib import Path
from datetime import date
from rich.console import Console
from rich.table import Table

console = Console()
MANIFEST = Path(__file__).parent / "repos.yaml"

def run(cmd):
    """Run a shell command and return stdout, raise on error."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        console.print(f"[red]Error:[/red] {result.stderr.strip()}")
        sys.exit(result.returncode)
    return result.stdout.strip()

def get_owner():
    """Return the current authenticated GitHub user/owner."""
    return run(["gh", "api", "user", "--jq", ".login"])

OWNER = get_owner()

def update_readme(repo, banner=None):
    """Insert or update archive banner in README.md."""
    tmpdir = Path(run(["mktemp", "-d"]))
    run(["git", "clone", f"git@github.com:{OWNER}/{repo}.git", str(tmpdir)])
    readme = tmpdir / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.exists() else ""
    
    banner_pattern = re.compile(r"^> \*\*⚠️ Archived [^\n]*\*\*.*(?:\n\n)?", re.MULTILINE)

    if banner:  # archiving → add or replace
        if banner_pattern.search(text):
            new_text = banner_pattern.sub(f"{banner}\n\n", text, count=1)
        else:
            new_text = f"{banner}\n\n{text}"
    else:  # unarchiving → strip any existing banner
        new_text = banner_pattern.sub("", text)

    if new_text != text:
        readme.write_text(new_text, encoding="utf-8")
        run(["git", "-C", str(tmpdir), "add", "README.md"])
        run(["git", "-C", str(tmpdir), "commit", "-m", "docs: sync archive banner"])
        run(["git", "-C", str(tmpdir), "push", "origin", "HEAD"])

def get_repo_info(repo):
    try:
        result = run(["gh", "api", f"repos/{OWNER}/{repo}", "--jq", "."])
        return json.loads(result)
    except CalledProcessError:
        console.print(f"[red]Repo {repo} not found or inaccessible[/red]")
        return None

def process_repo(repo_cfg, dry_run=False):
    repo = repo_cfg["name"]
    status = repo_cfg["status"]
    desc = repo_cfg.get("description", "")
    successor = repo_cfg.get("successor")
    archive_date = repo_cfg.get("archive_date") or str(date.today())

    console.print(f"\n[bold]Processing {repo}[/bold] (status={status})")

    if dry_run:
        console.print(f"  [cyan]Would set description:[/cyan] {desc}")
        return
    
    info = get_repo_info(repo)
    if not info:
        return  # skip deleted/missing repos

    if status == "archived":
        was_archived = info.get("archived", False)

        if was_archived:
            run(["gh", "repo", "unarchive", f"{OWNER}/{repo}", "--yes"])

        banner = f"> **⚠️ Archived {archive_date}. No longer maintained.**"
        if successor:
            banner += f" Successor: [{successor}](https://github.com/{OWNER}/{successor})."
        update_readme(repo, banner)

        run(["gh", "repo", "edit", f"{OWNER}/{repo}", "--description", desc])

        # Re-archive if needed
        run(["gh", "repo", "archive", f"{OWNER}/{repo}", "--yes"])

    elif status == "private":
        if info.get("private", False):
            console.print(f"  [green]Already private[/green]")
        else:
            run(["gh", "repo", "edit", f"{OWNER}/{repo}", "--visibility", "private"])
            run(["gh", "repo", "edit", f"{OWNER}/{repo}", "--description", desc])
            update_readme(repo, banner=None)  # remove archive banner if present

    elif status == "delete":
        console.print(f"[yellow]Skipping delete for {repo} (safety).[/yellow]")
        update_readme(repo, banner=None)  # remove archive banner if present

    else:  # active or other statuses
        if info.get("archived", False):
            run(["gh", "repo", "unarchive", f"{OWNER}/{repo}"])
        
        run(["gh", "repo", "edit", f"{OWNER}/{repo}", "--description", desc])
        update_readme(repo, banner=None)  # remove archive banner if present

def display_plan(manifest):
    table = Table(title="Repo Gardener - Plan")
    table.add_column("Repo")
    table.add_column("Status")
    table.add_column("Description")

    for repo_cfg in manifest["repos"]:
        table.add_row(repo_cfg["name"], repo_cfg["status"], repo_cfg.get("description", ""))
    console.print(table)

def generate_profile_readme_content(yaml_file="repos.yaml", output="PROFILE_README.md"):
    with open(yaml_file) as f:
        data = yaml.safe_load(f)

    repos = data["repos"]

    sections = {
        "active": "## 🚀 Active Projects",
        "reference": "## 🛠️ Useful References",
        "archived": "## 🗄️ Archived Experiments"
    }

    grouped = {"active": [], "reference": [], "archived": []}
    for repo in repos:
        if repo["status"] in ("private", "delete"):
            continue
        if repo["status"] == "active":
            grouped["active"].append(repo)
        elif repo["status"] == "archived" and repo["category"] in ("work", "experiment"):
            grouped["archived"].append(repo)
        else:
            grouped["reference"].append(repo)

    lines = []

    for key, header in sections.items():
        if grouped[key]:
            lines.append("")
            lines.append(header)
            for r in grouped[key]:
                lines.append(f'- [{r["name"]}](https://github.com/{OWNER}/{r["name"]}) — {r["description"]}')

    Path(output).write_text("\n".join(lines))
    print(f"Generated profile README at {output}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Repo Gardener")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without applying")
    args = parser.parse_args()

    manifest = yaml.safe_load(MANIFEST.read_text())
    display_plan(manifest)

    for repo_cfg in manifest["repos"]:
        process_repo(repo_cfg, dry_run=args.dry_run)

    generate_profile_readme_content()

if __name__ == "__main__":
    main()