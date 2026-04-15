# PST Resume Analyzer

Analyzes an Outlook `.pst` email archive and extracts resume-relevant information — projects, skills, achievements, and responsibilities — from thousands of work emails. Extraction can be tailored to a specific target role.

## Features

- Streams through large `.pst` files without loading everything into memory
- Skips non-work folders (deleted items, spam, travel, expenses, etc.)
- **Role-aware extraction** — focus results on what matters for a specific position
- Batches emails for efficient API usage
- Auto-saves checkpoints every 10 batches so long runs can be resumed
- Outputs a human-readable `.txt` report and structured `.json` file
- Fully configurable via `config.yaml` or CLI flags

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/nrsundar/pst-resume-analyzer.git
cd pst-resume-analyzer
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Set your API key

```bash
cp .env.example .env
# Edit .env and paste your API key
```

### 4. Configure your PST path

Edit `config.yaml` and set `pst_path` to the location of your `.pst` file:

```yaml
pst_path: "C:\\Users\\you\\Documents\\Outlook Files\\archive.pst"
```

## Usage

```bash
# Full run (reads all settings from config.yaml)
python analyze.py

# Tailor extraction for a specific target role
python analyze.py --role "Sr.SA Manager"
python analyze.py --role "Principal Solutions Architect"
python analyze.py --role "Director of Cloud Engineering"

# Test with just 200 emails first (recommended before a full run)
python analyze.py --test 200

# List all folders in the PST with message counts
python analyze.py --folders

# Resume an interrupted run from the last checkpoint
python analyze.py --resume

# Override PST path or output directory on the fly
python analyze.py --pst "D:\backup\old.pst" --output "results"
```

## Cost Estimate

| Model | ~85k emails | Quality |
|---|---|---|
| `claude-sonnet-4-6` (default) | ~$70–90 | Best |
| `claude-opus-4-6` | ~$300–350 | Highest |
| `claude-haiku-4-5-20251001` | ~$6–9 | Good |

Run `--test 200` first to verify results before committing to a full run.

## Output

Results are written to the `output/` directory:

- `resume_extraction.txt` — human-readable report with projects, skills, achievements, responsibilities, and collaborations
- `resume_extraction.json` — structured JSON for further processing

## Configuration

All settings live in `config.yaml`:

| Setting | Default | Description |
|---|---|---|
| `pst_path` | *(required)* | Path to your `.pst` file |
| `output_dir` | `output` | Where to write results |
| `role` | *(blank)* | Target role to tailor extraction toward |
| `model` | `claude-sonnet-4-6` | AI model to use |
| `batch_size` | `50` | Emails per API call |
| `max_body_chars` | `500` | Max email body length |
| `skip_folders` | see config | Folder names to ignore |

## Privacy

- Your `.env` (API key) and `output/` (extracted email data) are excluded from git via `.gitignore`
- Your `.pst` file is never uploaded or transmitted — only short text excerpts are sent to the API for analysis
