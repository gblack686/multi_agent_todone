# Windows Setup Guide for Multi-Agent Task System

This document outlines the modifications needed to run the multi-agent task system on Windows.

---

## 🔧 Required Modifications

### 1. Environment Configuration (`.env` file)

Create or update `.env` file in the project root with:

```bash
# Claude Code CLI Configuration
CLAUDE_CODE_PATH=C:\Users\gblac\AppData\Roaming\npm\claude.cmd

# Anthropic API Key (required)
ANTHROPIC_API_KEY=your-valid-anthropic-api-key-here

# Optional: GitHub Personal Access Token
GITHUB_PAT=your-github-pat

# Optional: Other services
E2B_API_KEY=your-e2b-key
CLOUDFLARED_TUNNEL_TOKEN=your-token
```

**Key Points:**
- `CLAUDE_CODE_PATH` must point to the `.cmd` file (not `.ps1`)
- The API key must be valid and active
- Without a valid API key, you'll get "Connection error"

---

### 2. UTF-8 Encoding Fix (Permanent Solution)

**Problem:** PowerShell console doesn't support emoji characters by default, causing:
```
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f680'
```

**Solution:** Apply the registry fix

#### Method A: Double-click the registry file
1. Double-click `enable_python_utf8.reg`
2. Click "Yes" when prompted
3. Close and reopen any terminals

#### Method B: Set manually in System Environment Variables
1. Open **System Properties → Environment Variables**
2. Under **System variables**, click **New**
3. Name: `PYTHONUTF8`
4. Value: `1`
5. Click OK and restart terminals

#### Method C: Temporary (per-session)
```powershell
$env:PYTHONUTF8='1'
```
Run this before each script execution.

---

### 3. Code Modifications to `adws/adw_modules/agent.py`

#### A. Added Windows Environment Variables

**Location:** `get_safe_subprocess_env()` function (lines 79-114)

Added critical Windows environment variables that Claude Code needs:

```python
# Windows-specific environment variables (critical for Claude Code)
"USERPROFILE": os.getenv("USERPROFILE"),  # User home directory on Windows
"LOCALAPPDATA": os.getenv("LOCALAPPDATA"),  # For cache/credentials
"APPDATA": os.getenv("APPDATA"),  # For application data
"TEMP": os.getenv("TEMP"),  # Temp directory
"TMP": os.getenv("TMP"),  # Alternative temp directory
"SystemRoot": os.getenv("SystemRoot"),  # Windows system root
"COMPUTERNAME": os.getenv("COMPUTERNAME"),  # Computer name
```

**Why this is critical:**
- Without `USERPROFILE`, Claude can't access cached credentials
- Without `APPDATA`/`LOCALAPPDATA`, Claude can't store configuration
- Without `TEMP`/`TMP`, Claude can't create temporary files
- This was the root cause of the "hangs after initialization" issue

#### B. Subprocess Execution Fixes

**Location:** `prompt_claude_code()` function (lines 425-436)

```python
result = subprocess.run(
    cmd,
    stdin=subprocess.DEVNULL,  # Don't wait for stdin
    stdout=output_f,
    stderr=subprocess.PIPE,
    text=True,
    env=env,
    cwd=request.working_dir,
    timeout=300,  # 5 minute timeout
    shell=True,  # Required for .cmd files on Windows
)
```

**Changes made:**
1. **`stdin=subprocess.DEVNULL`** - Prevents subprocess from hanging waiting for input
2. **`timeout=300`** - 5-minute safety timeout to prevent infinite hangs
3. **`shell=True`** - Required for Windows `.cmd` files to execute properly

#### C. API Key Handling

**Location:** `get_safe_subprocess_env()` function (line 82)

```python
# NOTE: Commented out to let Claude use cached credentials
# "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
```

**Rationale:**
- Claude Code CLI prefers to use cached credentials from `claude auth login`
- Passing API key via environment variable can cause connection issues on Windows
- Let Claude find credentials from Windows credential store

---

## ✅ Verification Steps

### 1. Test Claude CLI directly
```powershell
claude --version
# Should output: 2.0.24 (Claude Code)
```

### 2. Test with a simple prompt
```powershell
$env:PYTHONUTF8='1'  # Temporary UTF-8 fix if registry not applied
python adws/adw_prompt.py "What is 2+2?"
```

**Expected output:**
```
┌─── ✅ Success ───┐
│  2+2 equals 4.   │
└──────────────────┘
```

### 3. Test with uv run
```powershell
$env:PYTHONUTF8='1'
uv run adws/adw_prompt.py "Say hello in 3 words"
```

---

## 🐛 Common Issues and Solutions

### Issue 1: "Claude Code CLI is not installed"
**Cause:** `CLAUDE_CODE_PATH` not set or pointing to wrong file

**Solution:**
```powershell
# Find the correct path
where.exe claude

# Add to .env (use the .cmd file!)
CLAUDE_CODE_PATH=C:\Users\YourName\AppData\Roaming\npm\claude.cmd
```

---

### Issue 2: "API Error: Connection error"
**Causes:**
1. Invalid or expired API key
2. Missing Windows environment variables in subprocess

**Solutions:**
1. Update API key in `.env`:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ```
2. Ensure `adws/adw_modules/agent.py` includes Windows env vars (see Section 3A above)

**Test API key directly:**
```powershell
claude "Say hello"
# Should respond without errors
```

---

### Issue 3: Emoji/Unicode errors
**Cause:** Windows console encoding is cp1252 by default

**Solutions:**
- **Permanent:** Apply `enable_python_utf8.reg` (see Section 2)
- **Temporary:** Run `$env:PYTHONUTF8='1'` before each script

---

### Issue 4: Subprocess hangs indefinitely
**Cause:** Missing `stdin=subprocess.DEVNULL` or Windows environment variables

**Solution:** Ensure `adws/adw_modules/agent.py` includes all fixes from Section 3B

---

## 📁 Modified Files Summary

| File | Modification | Required? |
|------|-------------|-----------|
| `.env` | Add `CLAUDE_CODE_PATH` and `ANTHROPIC_API_KEY` | ✅ Yes |
| `adws/adw_modules/agent.py` | Add Windows env vars + subprocess fixes | ✅ Yes |
| `enable_python_utf8.reg` | Apply registry fix for UTF-8 | ⚠️ Recommended |
| System Environment Variables | Set `PYTHONUTF8=1` | ⚠️ Alternative to .reg |

---

## 🚀 Quick Start Commands

After applying all fixes:

```powershell
# 1. Test basic functionality
python adws/adw_prompt.py "What is 2+2?"

# 2. Create a hello world script
python adws/adw_prompt.py "Write a simple hello world Python script"

# 3. Run with specific model
python adws/adw_prompt.py "Explain this code" --model opus

# 4. Execute slash command
python adws/adw_slash_command.py /chore "Add logging"

# 5. Complex workflow
python adws/adw_chore_implement.py "Add error handling"
```

---

## 🔍 Debugging Tips

### Enable verbose output
Check the generated output files:
```powershell
# View raw JSONL stream
Get-Content agents\<adw_id>\oneoff\cc_raw_output.jsonl

# View summary
Get-Content agents\<adw_id>\oneoff\cc_raw_output_summary.json
```

### Check subprocess environment
```powershell
python -c "import os; print('USERPROFILE:', os.getenv('USERPROFILE')); print('APPDATA:', os.getenv('APPDATA'))"
```

### Test Claude credentials
```powershell
# Check if Claude is authenticated
claude auth show

# Re-authenticate if needed
claude auth login
```

---

## 📝 Notes

1. **Always use `.cmd` files** - On Windows, npm creates both `.ps1` and `.cmd` wrappers. Use `.cmd` for subprocess compatibility.

2. **Shell execution required** - Windows batch/cmd files need `shell=True` in `subprocess.run()` to execute properly.

3. **Environment variable inheritance** - Python subprocesses don't inherit all parent environment variables by default, especially user-specific Windows paths.

4. **API key caching** - Claude Code stores credentials in Windows Credential Manager. If available, it's more reliable than passing via environment variables.

5. **UTF-8 encoding** - PowerShell uses legacy codepages (cp1252) by default. Modern applications need UTF-8 mode enabled.

---

## ✅ Final Checklist

- [ ] `.env` file created with `CLAUDE_CODE_PATH` and `ANTHROPIC_API_KEY`
- [ ] `adws/adw_modules/agent.py` updated with Windows environment variables
- [ ] `adws/adw_modules/agent.py` updated with subprocess fixes (`stdin`, `shell=True`, `timeout`)
- [ ] UTF-8 registry fix applied (or using `$env:PYTHONUTF8='1'`)
- [ ] Tested with simple prompt: `python adws/adw_prompt.py "test"`
- [ ] Verified Claude CLI works: `claude --version`

Once all items are checked, the system should work reliably on Windows! 🎉

