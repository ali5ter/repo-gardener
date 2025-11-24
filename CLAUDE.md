# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`repo-gardener` is a Python tool that manages GitHub repository states from a single source of truth (`repos.yaml`). It enforces repository status (archived, active, private, delete), updates README files with archive banners, and generates profile README content.

## Development Commands

### Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running the tool
```bash
# Apply changes to repos
./.venv/bin/python gardener.py

# Dry run to preview changes (shows what will change including archive dates)
./.venv/bin/python gardener.py --dry-run
```

### Dependencies
- PyYAML: for parsing repos.yaml
- rich: for terminal output formatting
- GitHub CLI (gh): required for all GitHub API operations

## Architecture

### Core Flow (gardener.py)

1. **Load manifest**: Reads `repos.yaml` as single source of truth
2. **Display plan**: Shows repos and their target states in a table
3. **Process each repo**: Applies status changes via GitHub API
4. **Generate profile**: Creates `PROFILE_README.md` with categorized repos

### Key Functions

- `process_repo()` (line 105): Main orchestration - handles all status transitions
  - Archives/unarchives repos
  - Updates descriptions
  - Manages README archive banners
  - Changes visibility (public/private)
  - In dry-run mode: fetches README to show archive date changes

- `get_readme_content()` (line 40): Fetches README via GitHub API without cloning
  - Used in dry-run mode for fast preview
  - Decodes base64 content from API response

- `extract_archive_date()` (line 35): Extracts date from existing archive banner
  - Returns None if no banner exists
  - Used for preserving historical dates

- `update_readme()` (line 54): Clones repo, modifies README.md with archive banner
  - Uses regex to find/replace existing banners
  - Commits and pushes changes
  - Banner format: `> **⚠️ Archived YYYY-MM-DD. No longer maintained.**`

- `generate_profile_readme_content()` (line 165): Groups repos by status/category
  - Excludes private/delete repos
  - Creates markdown sections for active/reference/archived

### Important Implementation Details

**Dry-run mode** (line 115-140):
- Fetches README via API (no cloning) to check existing archive dates
- Shows archive date status:
  - Green "(preserved)" - existing date will be kept
  - Yellow "(new)" - new archive with today's date
  - Yellow "old → new (override)" - explicit date change in repos.yaml
- Displays successor links if configured

**Archive date preservation** (line 54-77):
- Archive dates are treated as historical information
- If a repo is already archived with a date in its README banner, that date is preserved
- Only uses today's date when initially archiving a repo (no existing banner)
- Users can explicitly override by setting `archive_date` in repos.yaml
- Uses special "auto" value internally to signal date preservation logic

**Archiving workflow** (line 146-157):
- Always unarchives first if already archived (GitHub API limitation - can't edit archived repos)
- Updates README with archive banner (preserving historical date)
- Sets description
- Re-archives the repo

**Status types**:
- `archived`: Public but frozen, gets archive banner in README
- `private`: Makes repo private, removes archive banner
- `active`: Unarchives and removes banner
- `delete`: Skipped for safety (manual deletion required)

**GitHub CLI usage**: All operations use `gh` CLI via subprocess
- Authentication: Uses current `gh` auth session
- Owner detection: `gh api user --jq .login` (line 31)

### Configuration File (repos.yaml)

Not committed to git (use `repos.yaml.template` as starting point). Each repo entry:
- `name`: GitHub repo name (required)
- `status`: active | archived | private | delete
- `category`: experiment | utility | work | showcase | personal
- `description`: Used as GitHub repo description
- `successor`: Optional link to replacement repo (shown in archive banner)
- `archive_date`: Optional YYYY-MM-DD format
  - If omitted, preserves existing date from README or uses today's date for newly archived repos
  - If specified, overrides the date (useful for backdating or corrections)

Categories are used for grouping in generated profile README:
- `active` repos → "🚀 Active Projects"
- `archived` with work/experiment category → "🗄️ Archived Experiments"
- Others → "🛠️ Useful References"
