# Windows Quick Fix Cheat Sheet

## 🚨 Essential Fixes (Apply These First)

### 1. Update `.env` file
```bash
CLAUDE_CODE_PATH=C:\Users\gblac\AppData\Roaming\npm\claude.cmd
ANTHROPIC_API_KEY=your-valid-api-key-here
```

### 2. Fix UTF-8 encoding
**Double-click `enable_python_utf8.reg` → Click "Yes" → Restart terminal**

Or temporarily: `$env:PYTHONUTF8='1'` before each command

---

## ✅ Run Your First Command

```powershell
# Simple test
python adws/adw_prompt.py "What is 2+2?"

# Should output: ✅ Success | 2+2 equals 4.
```

---

## 🐛 Quick Troubleshooting

| Error | Fix |
|-------|-----|
| "Claude Code CLI is not installed" | Add `CLAUDE_CODE_PATH=...\.cmd` to `.env` |
| "API Error: Connection error" | Update `ANTHROPIC_API_KEY` in `.env` |
| "UnicodeEncodeError" | Apply `enable_python_utf8.reg` |
| Hangs forever | Check `adws/adw_modules/agent.py` has Windows env vars |

---

## 📋 What Changed in Code

**File:** `adws/adw_modules/agent.py`

**Lines 100-106:** Added Windows environment variables
```python
"USERPROFILE": os.getenv("USERPROFILE"),
"LOCALAPPDATA": os.getenv("LOCALAPPDATA"),
"APPDATA": os.getenv("APPDATA"),
"TEMP": os.getenv("TEMP"),
"TMP": os.getenv("TMP"),
"SystemRoot": os.getenv("SystemRoot"),
```

**Lines 427-436:** Fixed subprocess execution
```python
subprocess.run(
    cmd,
    stdin=subprocess.DEVNULL,  # ← Added
    timeout=300,                # ← Added
    shell=True,                 # ← Added (for .cmd files)
    ...
)
```

---

## ✅ Verification

```powershell
# 1. Test Claude CLI
claude --version
# → 2.0.24 (Claude Code)

# 2. Test Python script
python adws/adw_prompt.py "Say hello"
# → ✅ Success

# 3. Check environment
python -c "import os; print(os.getenv('USERPROFILE'))"
# → C:\Users\gblac
```

---

**See [`WINDOWS_SETUP.md`](WINDOWS_SETUP.md) for complete details**

