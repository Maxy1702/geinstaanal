# IQOS Social Intelligence - Setup Guide

## 🚀 Quick Start (New PC)

### Option A: Automated Setup (Recommended)

**Windows:**
```bash
# After cloning, just run:
setup.bat
```

**Mac/Linux:**
```bash
# After cloning, just run:
chmod +x setup.sh
./setup.sh
```

The script will automatically:
- ✅ Create virtual environment
- ✅ Install all dependencies  
- ✅ Verify setup works

---

### Option B: Manual Setup

### 1. Prerequisites
- Python 3.10+ installed
- Git installed
- VS Code (recommended)

### 2. Clone Repository
```bash
git clone https://github.com/Maxy1702/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

### 3. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
```

**Mac/Linux:**
```bash
python3 -m venv venv
```

### 4. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### 5. Install Dependencies
```bash
pip install -r requirements.txt
```

### 6. Copy Data Files (Manual Transfer)

The following files are **NOT** in git (too large) and must be transferred manually:

- `data/input/dataset_instagram-scraper_2025-10-21_12-40-20-239.json` (47 MB)
- `data/images/*.jpg` (downloaded images)

**Copy them to:**
```
YOUR_REPO_NAME/
└── data/
    ├── input/     ← Place JSON file here
    └── images/    ← Place image files here
```

### 7. Verify Setup
```bash
python3 run_analysis.py
```

Should show: Parsing 2,629 posts ✅

---

## 🔧 VS Code Setup (Automatic)

If using VS Code, the workspace settings in `.vscode/settings.json` will:
- ✅ Auto-select the `venv` Python interpreter
- ✅ Auto-activate venv in terminal
- ✅ Configure Python paths

**Just open the folder in VS Code and it works!**

---

## 📦 Project Structure

```
geinstaanal/
├── .vscode/              # VS Code workspace settings (committed)
├── config/               # Configuration files
├── data/                 # Data files (NOT in git)
│   ├── input/           # Instagram dataset (manual transfer)
│   ├── images/          # Downloaded images (manual transfer)
│   └── processed/       # Progress tracking
├── output/              # Generated reports and logs
├── src/                 # Python source code
├── venv/                # Virtual environment (NOT in git)
├── .gitignore           # Git ignore rules
├── requirements.txt     # Python dependencies
├── run_analysis.py      # Main script
└── README.md            # Project documentation
```

---

## 🔄 Workflow

### First Time Setup
1. Clone repo
2. Create venv
3. Install requirements
4. Copy data files

### Daily Development
1. Activate venv: `source venv/bin/activate`
2. Make changes
3. Run tests: `python3 run_analysis.py`
4. Commit: `git add . && git commit -m "message"`
5. Push: `git push`

---

## 🐛 Troubleshooting

### VS Code Not Finding Python Interpreter
1. Press `Cmd/Ctrl + Shift + P`
2. Type: "Python: Select Interpreter"
3. Choose `./venv/bin/python`

### Packages Not Found
```bash
# Make sure venv is activated
source venv/bin/activate  # Mac/Linux
# Then reinstall
pip install -r requirements.txt
```

### Data Files Missing
- Check `data/input/` has the JSON file
- Check `data/images/` has image files
- These must be transferred manually (not in git)

---

## 📚 Next Steps

After setup is complete:
1. Install LM Studio: https://lmstudio.ai/
2. Load vision model (LLaVA-1.6-Mistral-7B)
3. Continue to Phase 2B: LLM integration