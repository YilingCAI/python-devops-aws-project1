# Dependabot Quick Reference

## 🎯 What is Dependabot?

Automated dependency management that:
- Creates PRs for dependency updates
- Runs CI/CD on each PR
- Optionally auto-merges when tests pass
- Keeps your stack secure and up-to-date

---

## 📅 Update Schedule

```
Monday 02:00 UTC  → Poetry (Python)
Monday 03:00 UTC  → Docker Frontend
Monday 03:30 UTC  → Docker Backend
Tuesday 04:00 UTC → Terraform
Wed 02:00 UTC     → GitHub Actions
```

**Time Zone:** UTC (adjust to your local time if needed)

---

## 📊 Open PR Limits

| Ecosystem | Max PRs |
|-----------|---------|
| Poetry | 5 |
| Docker | 2 each |
| Terraform | 3 |
| GitHub Actions | 4 |

**Maximum total:** ~14 PRs at once

---

## 🏷️ PR Labels

```
backend      → Python dependencies
docker       → Base image updates
infra        → Terraform providers/modules
ci           → GitHub Actions
dependencies → All dependency updates
terraform    → Terraform-specific
```

---

## 🔄 Types of Updates

### Patch Updates (Auto-merge ✅)
```
1.2.3 → 1.2.4
```
- Bug fixes, security patches
- Safe to merge automatically
- No breaking changes

### Minor Updates (Auto-merge ✅)
```
1.2.3 → 1.3.0
```
- New features, backwards compatible
- Generally safe to auto-merge
- May need testing

### Major Updates (Manual review ⚠️)
```
1.2.3 → 2.0.0
```
- Breaking changes possible
- Requires manual testing
- Must review carefully

---

## 🚀 Auto-Merge Workflow

**Triggers on:**
- PR from `dependabot[bot]`
- CI tests complete
- All checks pass ✅

**Then:**
1. Waits for CI to pass (max 30 min)
2. Enables auto-merge (squash strategy)
3. GitHub auto-merges when ready
4. Comments with status

**If CI fails:**
- ❌ No auto-merge
- Posts failure comment
- Requires manual review

---

## 🔐 Security

**Dependabot PRs:**
- ✅ Run full CI/CD pipeline
- ✅ Include security scans
- ✅ No AWS credentials used
- ✅ Secrets stay in AWS Secrets Manager

**CI Checks:**
- Trivy filesystem scan
- Bandit (Python security)
- ESLint (JavaScript linting)
- TypeScript type checking
- Unit tests
- Integration tests

---

## 📍 Important Files

**Main Configuration:**
```
.github/dependabot.yml              ← Dependabot settings
.github/workflows/ci.yml            ← CI/CD pipeline
.github/workflows/dependabot-auto-merge.yml  ← Auto-merge
```

**Dependency Files:**
```
backend/poetry.lock                 ← Python dependencies
backend/Dockerfile                  ← Backend image
frontend/package-lock.json          ← JavaScript dependencies
frontend/Dockerfile                 ← Frontend image
infra/.terraform.lock.hcl           ← Terraform lock
```

---

## ⚙️ How It Works

### Python (Poetry)

**What:** Updates `poetry.lock`
**Trigger:** `pyproject.toml` changes
**Example:**
```
poetry add fastapi==0.104.1  # Developer adds
Dependabot creates PR → CI tests → Auto-merge
```

**Ignored Dependency:**
- `pycrypto` (requires manual migration)
- Reason: Deprecated, needs code changes
- Manual steps required

### Docker

**What:** Updates base image versions
**Examples:**
- `python:3.12-slim` → `python:3.12.1-slim`
- `node:20-alpine` → `node:20.10-alpine`

**Impact:**
- Security patches applied
- May include Python/Node.js updates
- Cached Docker layers invalidated

### Terraform

**What:** Updates provider versions
**Example:**
```
aws provider ~> 5.0  →  aws provider ~> 5.47
```

**Impact:**
- New AWS resources available
- Bug fixes from HashiCorp
- Infrastructure validated via CI

### GitHub Actions

**What:** Updates action versions
**Examples:**
- `actions/checkout@v4`
- `docker/build-push-action@v4`
- `hashicorp/setup-terraform@v2`

**Impact:**
- Security patches
- Performance improvements
- New features

---

## 🎯 Common Scenarios

### Scenario 1: Patch Update
```
✅ Auto-merged automatically
Timeline: Created Mon → Merged same day
Impact: Minimal (bug fix/patch)
```

### Scenario 2: Minor Update
```
✅ Auto-merged after CI passes
Timeline: Created Mon → Merged Mon/Tue
Impact: New feature, backward compatible
```

### Scenario 3: Major Update
```
⚠️  Manual review required
Timeline: Created → Requires testing
Impact: Possible breaking changes
Action: Review CI logs, test locally
```

### Scenario 4: CI Fails
```
❌ Not auto-merged
Timeline: Created → CI fails → Manual
Action: Investigate error, fix, rerun
```

---

## 🔧 Management Commands

**View Dependabot PRs:**
```bash
gh pr list --search "author:dependabot"
```

**View specific PR:**
```bash
gh pr view <NUMBER>
```

**Check PR status:**
```bash
gh pr checks <NUMBER>
```

**Merge manually (if needed):**
```bash
gh pr merge <NUMBER> --squash
```

**Close PR (don't want update):**
```bash
gh pr close <NUMBER>
```

---

## ⚠️ Important Notes

**DO:**
- ✅ Review CI logs if PR created
- ✅ Understand what's being updated
- ✅ Test locally if concerned
- ✅ Monitor PR merge activity

**DON'T:**
- ❌ Manually edit lock files
- ❌ Ignore failing CI checks
- ❌ Force merge without tests passing
- ❌ Disable Dependabot (keep it enabled)

---

## 🚨 Troubleshooting

### PRs not being created?

**Check 1:** Dependabot enabled
- Settings → Code security & analysis
- Scroll to Dependabot
- Verify "Enable" checked

**Check 2:** PR limit not reached
- `.github/dependabot.yml`
- Check `open-pull-requests-limit`

**Check 3:** Dependencies actually changed
- Last check date visible in settings

### CI not running on PRs?

**Check:**
- PR targets: main, develop, or staging
- `.github/workflows/ci.yml` has `pull_request` trigger
- No branch protection requiring approval first

### Auto-merge not working?

**Check:**
- `.github/workflows/dependabot-auto-merge.yml` exists
- CI must pass 100%
- No required approvals blocking merge
- GitHub app permissions correct

---

## 📈 Monitoring

**Weekly Tasks:**
- [ ] Check Dependabot PRs created
- [ ] Verify CI passes
- [ ] Monitor auto-merge rate
- [ ] Note any failures

**What to Track:**
- Number of PRs merged
- Auto-merged vs manual
- Average merge time
- CI failure rate

---

## 🔗 Links

- **Configuration:** `.github/dependabot.yml`
- **Auto-merge:** `.github/workflows/dependabot-auto-merge.yml`
- **Full Guide:** `docs/DEPENDABOT_SETUP.md`
- **GitHub Docs:** https://docs.github.com/en/code-security/dependabot

---

## ✨ Summary

```
Dependabot = Automated Dependency Updates

Every week:
  • Poetry deps updated
  • Docker images patched
  • Terraform providers upgraded
  • GitHub Actions updated

Each PR:
  • Full CI/CD runs
  • Security scans execute
  • Tests validate changes
  • Auto-merges if ✅ passed

Result:
  • Dependencies always current
  • Security patches applied immediately
  • Minimal manual work
  • Clean git history
```

**Status:** ✅ Enabled and monitoring
