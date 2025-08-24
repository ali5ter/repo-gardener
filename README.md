# 🌱 Repo Gardener

`repo-gardener` helps you manage and curate your GitHub repositories from a single source of truth.

## Features

- Archive or unarchive repositories based on a configuration file
- Ensure each archived repo has an **archive notice** in its `README.md`
- Future extension: add topics, labels, descriptions, or other curation metadata
- Generate markdown content listing categrized repos you could include in your GitHub Profile README

## Curation of your repos

When looking at repos, decide if they should be:

- Active (you’ll maintain them)
- Archived but kept public (still useful as reference)
- Archived and made private (not worth public exposure)
- Deleted (true dead ends with no value)

Consider how you'd categorize your repos:

- showcase: Highlight in your GitHub Profile README
- utility: Helper scripts/tools, maybe private
- experiment: One-off explorations, often archived
- work: Work related or professional projects
- personal: Things you want to keep, not showcase

Use the repos.yaml to identify these states and add any metadata, e.g.

```yaml
repos:
  - name: my-old-repo
    status: archived
    category: experiment
    description: "Old experiment, archived in favor of new-repo"
    successor: new-repo
    archive_date: 2025-08-16

  - name: personal-scripts
    status: private
    category: personal
    description: "Utility scripts for personal use"

  - name: prototype-demo
    status: active
    category: showcase
    description: "Demo project still in development"
```

Keep this file as the source of truth for the state of your repos. Run `gardener.py` to make sure this state is enforced in your GitHub account.

## Getting Started

### 1. Clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/repo-gardener.git
cd repo-gardener
```

### 2. Create a Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Copy the configuration template

The configuration file `repos.yaml` is your **single source of truth** for all repositories you manage.

```bash
cp repos.yaml.template repos.yaml
```

- Edit `repos.yaml` to define your repositories and their desired state.
- Do **not** edit `repos.yaml.template`. It is only a starting point.

### 4. Run the gardener

```bash
./.venv/bin/python gardener.py
```

This will:

- Archive/unarchive repositories as defined in `repos.yaml`
- Add archive notices to `README.md` files if needed
- Keep your repo description up to date
- Generate PROFILE_README.md which you can use in your GitHub Profile README