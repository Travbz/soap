# Software Development Lifecycle (SDLC)

This document describes the software development lifecycle for the Vending Machine Controller project, including our automated CI/CD workflows using GitHub Actions.

## Table of Contents

1. [Overview](#overview)
2. [Branch Strategy](#branch-strategy)
3. [Development Workflow](#development-workflow)
4. [Commit Message Standards](#commit-message-standards)
5. [Automated Testing (CI)](#automated-testing-ci)
6. [Automated Releases (CD)](#automated-releases-cd)
7. [Version Numbering](#version-numbering)
8. [Complete Example Workflow](#complete-example-workflow)

---

## Overview

Our SDLC is designed to ensure code quality, maintainability, and reliable releases through:

- **Conventional Commits** for semantic versioning
- **Automated Testing** on every pull request
- **Automated Releases** on merge to main/master
- **Semantic Versioning** (major.minor.patch)

We use two GitHub Actions workflows:

1. **PR Tests Workflow** (`.github/workflows/pr-tests.yml`) - Runs tests on pull requests
2. **Release Workflow** (`.github/workflows/release.yml`) - Creates releases on merge to main/master

---

## Branch Strategy

### Main Branches

- **`main`/`master`**: Production-ready code. Protected branch requiring pull requests.
- **Feature branches**: All development happens in feature branches.

### Branch Naming Convention

Use descriptive branch names with prefixes:

```
feature/add-payment-retry-logic
fix/flowmeter-calibration-error
refactor/centralize-config-values
docs/update-setup-guide
chore/update-dependencies
```

**Prefixes:**
- `feature/` - New features
- `fix/` - Bug fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation changes
- `chore/` - Maintenance tasks
- `test/` - Test additions or updates

---

## Development Workflow

### Step 1: Create a Feature Branch

```bash
# Pull latest changes
git checkout main
git pull origin main

# Create and switch to feature branch
git checkout -b feature/my-new-feature
```

### Step 2: Make Changes and Commit

Make your code changes, then commit using **Conventional Commits** format:

```bash
git add .
git commit -m "feat: add retry logic to payment processing"
```

See [Commit Message Standards](#commit-message-standards) for details.

### Step 3: Push Branch and Create Pull Request

```bash
# Push your branch to GitHub
git push origin feature/my-new-feature
```

Then create a pull request on GitHub targeting `main`/`master`.

### Step 4: Automated Testing

When you create or update a pull request, the **PR Tests Workflow** automatically runs:

1. ✅ Installs Python 3.7 (matches Raspberry Pi environment)
2. ✅ Installs dependencies using `uv` (fast package manager)
3. ✅ Runs payment protocol tests
4. ✅ Checks for Python syntax errors

**The PR will show a green checkmark** if all tests pass, or a **red X** if tests fail.

### Step 5: Code Review and Merge

1. Request a code review from team members
2. Address any feedback
3. Once approved and tests pass, **merge the PR** (use "Squash and merge" to keep history clean)

### Step 6: Automated Release

After merging to `main`/`master`, the **Release Workflow** automatically:

1. 📊 Analyzes commit messages since the last release
2. 📈 Determines version bump based on conventional commits:
   - `feat:` → Minor version bump (v1.0.0 → v1.1.0)
   - `fix:`, `refactor:`, `chore:`, `docs:` → Patch version bump (v1.0.0 → v1.0.1)
   - `BREAKING CHANGE:` or `!` → Major version bump (v1.0.0 → v2.0.0)
3. 🏷️ Creates a Git tag with the new version
4. 📦 Creates a GitHub Release with auto-generated release notes

---

## Commit Message Standards

We use **Conventional Commits** to enable automated semantic versioning.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types and Version Bumps

| Type | Description | Version Bump | Example |
|------|-------------|--------------|---------|
| `feat:` | New feature | **Minor** (v1.0.0 → v1.1.0) | `feat: add flowmeter calibration mode` |
| `fix:` | Bug fix | **Patch** (v1.0.0 → v1.0.1) | `fix: resolve done button false triggers` |
| `refactor:` | Code refactoring | **Patch** (v1.0.0 → v1.0.1) | `refactor: centralize config values` |
| `docs:` | Documentation only | **Patch** (v1.0.0 → v1.0.1) | `docs: update SDLC documentation` |
| `chore:` | Maintenance tasks | **Patch** (v1.0.0 → v1.0.1) | `chore: update dependencies` |
| `test:` | Add or update tests | **No release** | `test: add transaction result tests` |
| `BREAKING CHANGE:` | Breaking changes | **Major** (v1.0.0 → v2.0.0) | See below |

### Breaking Changes

For major version bumps, include `BREAKING CHANGE:` in the commit footer or add `!` after the type:

```bash
# Method 1: Using footer
git commit -m "feat: redesign payment protocol

BREAKING CHANGE: ePort protocol now requires firmware v2.0+"

# Method 2: Using ! after type
git commit -m "feat!: change configuration file format"
```

### Scope (Optional)

Add a scope to provide more context:

```bash
git commit -m "fix(payment): retry failed authorization requests"
git commit -m "refactor(config): centralize timing constants"
git commit -m "docs(setup): add Raspberry Pi installation steps"
```

### Good Commit Examples

```bash
# Feature (minor bump)
git commit -m "feat: add real-time flowmeter output display"

# Bug fix (patch bump)
git commit -m "fix: prevent motor control errors on GPIO conflicts"

# Refactor (patch bump)
git commit -m "refactor: extract payment retry logic into helper function"

# Documentation (patch bump)
git commit -m "docs: document SDLC workflow and GitHub Actions"

# Breaking change (major bump)
git commit -m "feat!: change config file from .py to .yaml format"

# No release (non-conventional commit)
git commit -m "Update README.md"
```

---

## Automated Testing (CI)

**Workflow File:** `.github/workflows/pr-tests.yml`

### Triggers

Runs automatically on:
- Pull request opened
- Pull request updated (new commits pushed)
- Pull request reopened

### What It Tests

1. **Payment Protocol Tests** - Verifies ePort communication logic:
   - CRC16 checksum calculation
   - Status command
   - Reset command
   - Authorization request
   - Transaction result sending
   - Transaction ID retrieval

2. **Syntax Validation** - Checks for Python syntax errors in:
   - `ePort/main.py`
   - `ePort/src/machine.py`
   - `ePort/src/payment.py`

### Environment

- **OS:** Ubuntu Latest
- **Python:** 3.7 (matches Raspberry Pi environment)
- **Package Manager:** `uv` (fast, modern Python package installer)
- **Dependencies:** `pyserial` (RPi.GPIO mocked in tests)

### Viewing Test Results

1. Go to your pull request on GitHub
2. Scroll to the bottom - you'll see "All checks have passed" or "Some checks failed"
3. Click "Details" to view full test output
4. Fix any failing tests before merging

---

## Automated Releases (CD)

**Workflow File:** `.github/workflows/release.yml`

### Triggers

Runs automatically when:
- Code is merged to `main` or `master` branch

### How It Works

1. **Fetch Commit History**
   - Retrieves all commits since the last release tag
   - Looks for conventional commit patterns

2. **Determine Version Bump**
   - Scans commit messages for `feat:`, `fix:`, `BREAKING CHANGE:`, etc.
   - Calculates the appropriate version bump:
     - `BREAKING CHANGE:` or `!` → Major (v1.0.0 → v2.0.0)
     - `feat:` → Minor (v1.0.0 → v1.1.0)
     - `fix:`, `refactor:`, `chore:`, `docs:` → Patch (v1.0.0 → v1.0.1)

3. **Create Git Tag**
   - Creates an annotated tag (e.g., `v1.2.3`)
   - Pushes tag to GitHub

4. **Generate Release Notes**
   - Creates a GitHub Release with:
     - Auto-generated changelog from commit messages
     - Emoji indicators (🚀 Major, ✨ Minor, 🐛 Patch)
     - List of all commits since last release

5. **Publish Release**
   - Release is visible on GitHub Releases page
   - Tag is available for `git checkout` or deployment

### Skipping Releases

The workflow will **skip creating a release** if:
- No new commits since last tag
- Only non-conventional commits (e.g., "Update README")
- Only `test:` or `style:` commits

### Release Notes Format

#### Major Release (v2.0.0)

```markdown
## 🚀 Major Release: v2.0.0

⚠️ **BREAKING CHANGES** - This release contains breaking changes.

### Changes

- feat!: change configuration file format to YAML
- refactor: remove deprecated GPIO pins
- docs: update setup guide for new config format

---

*This release was automatically generated from conventional commits.*
```

#### Minor Release (v1.1.0)

```markdown
## ✨ Minor Release: v1.1.0

New features and improvements.

### Changes

- feat: add real-time flowmeter output
- feat: implement retry logic for declined cards
- fix: resolve done button debounce issues

---

*This release was automatically generated from conventional commits.*
```

#### Patch Release (v1.0.1)

```markdown
## 🐛 Patch Release: v1.0.1

Bug fixes and patches.

### Changes

- fix: prevent GPIO conflicts on restart
- refactor: centralize timing configuration
- docs: add SDLC documentation

---

*This release was automatically generated from conventional commits.*
```

---

## Version Numbering

We use **Semantic Versioning** (SemVer): `MAJOR.MINOR.PATCH`

### Version Format

```
vMAJOR.MINOR.PATCH

Example: v1.3.2
         │ │ │
         │ │ └─ Patch: Bug fixes, refactors, docs
         │ └─── Minor: New features (backwards compatible)
         └───── Major: Breaking changes
```

### Version Bump Rules

| Change Type | Commit Type | Version Change | Example |
|-------------|-------------|----------------|---------|
| **Breaking Change** | `BREAKING CHANGE:` or `!` | `v1.3.2` → `v2.0.0` | New config format |
| **New Feature** | `feat:` | `v1.3.2` → `v1.4.0` | Add new payment method |
| **Bug Fix** | `fix:` | `v1.3.2` → `v1.3.3` | Fix payment timeout |
| **Refactor** | `refactor:` | `v1.3.2` → `v1.3.3` | Improve code structure |
| **Documentation** | `docs:` | `v1.3.2` → `v1.3.3` | Update README |
| **Maintenance** | `chore:` | `v1.3.2` → `v1.3.3` | Update dependencies |

### First Release

If no tags exist, the first release will be `v0.1.0`.

---

## Complete Example Workflow

Here's a complete example of developing and releasing a new feature:

### Scenario: Add Customer Receipt Printing

#### 1. Create Feature Branch

```bash
git checkout main
git pull origin main
git checkout -b feature/add-receipt-printing
```

#### 2. Develop the Feature

```bash
# Make code changes...
# Add receipt printer support to machine.py
# Update config with printer settings
# Add tests for receipt generation
```

#### 3. Commit Changes (Conventional Commit)

```bash
git add .
git commit -m "feat: add thermal receipt printing support

- Add receipt printer controller to machine.py
- Include transaction details on receipt
- Add RECEIPT_PRINTER_PORT to config
- Add receipt formatting tests"
```

#### 4. Push and Create Pull Request

```bash
git push origin feature/add-receipt-printing
```

Go to GitHub and create a pull request:
- **Title:** "Add thermal receipt printing support"
- **Description:** Explain the feature, testing done, etc.

#### 5. Automated Testing Runs

GitHub Actions automatically:
- ✅ Runs all tests with Python 3.7
- ✅ Checks syntax
- Shows results on PR page

#### 6. Code Review and Approval

Team reviews code, suggests changes, approves when ready.

#### 7. Merge Pull Request

Click "Squash and merge" on GitHub.

Squashed commit message (GitHub will use your PR commit messages):
```
feat: add thermal receipt printing support (#15)

- Add receipt printer controller to machine.py
- Include transaction details on receipt
- Add RECEIPT_PRINTER_PORT to config
- Add receipt formatting tests
```

#### 8. Automated Release Creation

GitHub Actions Release Workflow automatically:

1. Detects `feat:` commit → **Minor version bump**
2. Gets last version: `v1.2.0`
3. Bumps to: `v1.3.0`
4. Creates tag `v1.3.0`
5. Generates release notes:

```markdown
## ✨ Minor Release: v1.3.0

New features and improvements.

### Changes

- feat: add thermal receipt printing support (#15)

---

*This release was automatically generated from conventional commits.*
```

6. Publishes release on GitHub

#### 9. Deploy to Production

```bash
# On Raspberry Pi
cd ~/soap
git fetch --tags
git checkout v1.3.0
python3 -m ePort.main
```

---

## Best Practices

### Commits

- ✅ **DO** use conventional commit format
- ✅ **DO** write clear, descriptive commit messages
- ✅ **DO** commit logical, atomic changes
- ❌ **DON'T** use vague messages like "fix stuff" or "update code"
- ❌ **DON'T** commit unrelated changes together

### Pull Requests

- ✅ **DO** keep PRs focused on a single feature/fix
- ✅ **DO** wait for tests to pass before requesting review
- ✅ **DO** update documentation if needed
- ❌ **DON'T** merge without code review
- ❌ **DON'T** merge with failing tests

### Releases

- ✅ **DO** verify the version bump makes sense for your changes
- ✅ **DO** check release notes are accurate
- ✅ **DO** test the release on hardware before production deployment
- ❌ **DON'T** manually create releases (let automation handle it)
- ❌ **DON'T** skip testing after a release

---

## Troubleshooting

### Tests Failing on PR

1. View the test output by clicking "Details" on the failed check
2. Run tests locally: `python3 -m ePort.tests.test_payment`
3. Fix the issues and push again
4. Tests will automatically re-run

### No Release Created After Merge

Possible reasons:
- ❌ No conventional commits (e.g., "Update README" instead of "docs: update README")
- ❌ Only `test:` or `style:` commits (these don't trigger releases)
- ❌ No new commits since last tag

**Solution:** Ensure at least one commit uses conventional format with `feat:`, `fix:`, `refactor:`, `chore:`, or `docs:`

### Wrong Version Bump

If the wrong version was created:

1. Delete the tag locally and on GitHub:
   ```bash
   git tag -d v1.2.3
   git push origin :refs/tags/v1.2.3
   ```

2. Delete the GitHub Release from the Releases page

3. Fix commit message format if needed

4. Re-run the release workflow or manually create the correct version

### Tests Pass Locally But Fail in CI

Possible causes:
- Different Python version (CI uses 3.7)
- Missing dependencies
- File path issues

**Solution:** Test with Python 3.7 locally:
```bash
python3.7 -m ePort.tests.test_payment
```

---

## Additional Resources

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Semantic Versioning Specification](https://semver.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Project Setup Guide](SETUP.md)
- [Testing Documentation](TESTING.md)
- [Architecture Overview](ARCHITECTURE.md)

---

**Last Updated:** January 2026
