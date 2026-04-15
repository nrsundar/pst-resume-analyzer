# PST Resume Analyzer

Analyzes an Outlook `.pst` email archive and extracts resume-relevant information — projects, skills, achievements, and responsibilities — from thousands of work emails. Extraction can be tailored to a specific target role.

## Features

- Streams through large `.pst` files without loading everything into memory
- Skips non-work folders (deleted items, spam, travel, expenses, etc.)
- **Role-aware extraction** — focus results on what matters for a specific position
- **Two provider options** — use a direct API key or your existing AWS account via Bedrock
- Batches emails for efficient API usage
- Auto-saves checkpoints every 10 batches so long runs can be resumed
- Outputs a human-readable `.txt` report and structured `.json` file
- Fully configurable via `config.yaml` or CLI flags

---

## Kiro IDE / Kiro CLI

This project works seamlessly with [Kiro](https://kiro.dev) — an agentic AI IDE and CLI.

### Kiro IDE (Desktop)

Download and install from [kiro.dev](https://kiro.dev). Supports Windows 10/11 (64-bit), macOS (Intel & Apple Silicon), and Linux (glibc 2.39+, Ubuntu 24+, Fedora 40+).

1. Download the installer for your OS from [kiro.dev](https://kiro.dev)
2. Run the installer and follow the prompts
3. On first launch, authenticate with GitHub, Google, AWS Builder ID, or AWS IAM Identity Center
4. Open the cloned `pst-resume-analyzer` folder as your project

### Kiro CLI

**macOS / Linux**
```bash
curl -fsSL https://cli.kiro.dev/install | bash
```

**Windows** (PowerShell or Windows Terminal — not Command Prompt)
```powershell
irm 'https://cli.kiro.dev/install.ps1' | iex
```

**Linux — Ubuntu (.deb)**
```bash
wget https://desktop-release.q.us-east-1.amazonaws.com/latest/kiro-cli.deb
sudo dpkg -i kiro-cli.deb
sudo apt-get install -f
```

**Linux — AppImage**
```bash
wget https://desktop-release.q.us-east-1.amazonaws.com/latest/kiro-cli.appimage
chmod +x kiro-cli.appimage
./kiro-cli.appimage
```

> If you run into installation issues, run `kiro-cli doctor` to diagnose and fix common problems.

---

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

### 3. Choose your provider and configure credentials

You can run this tool using either **Option A (direct API key)** or **Option B (AWS Bedrock)**. Choose one.

---

#### Option A — Direct API Key

1. Get an API key from [console.anthropic.com/api-keys](https://console.anthropic.com/api-keys)
2. Copy `.env.example` to `.env` and paste your key:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```
3. In `config.yaml`, set:
   ```yaml
   provider: "anthropic"
   ```

---

#### Option B — AWS Bedrock (use your existing AWS account)

**Step 1 — Enable model access in the AWS Console**

1. Sign in to the [AWS Console](https://console.aws.amazon.com)
2. In the search bar, type **Bedrock** and open **Amazon Bedrock**
3. In the left sidebar, under **Bedrock configurations**, click **Model access**
4. Click **Modify model access** (or **Request model access**)
5. Find **Anthropic** in the list and check the models you want:
   - `Claude Opus 4.6` (recommended — highest quality)
   - `Claude Sonnet 4.6` (good balance of quality and cost)
   - `Claude Haiku 4.5` (fastest, cheapest)
6. Click **Next → Submit**. Approval is typically instant for most models.

> **Note:** Model availability varies by region. `us-east-1` (N. Virginia) and `us-west-2` (Oregon) have the widest selection.

**Step 2 — Set up AWS credentials**

Choose the method that matches your setup:

**Method 1 — AWS CLI (recommended)**

Install the AWS CLI and run:
```bash
aws configure
```
Enter your `AWS Access Key ID`, `AWS Secret Access Key`, and default region (e.g. `us-east-1`). Credentials are stored in `~/.aws/credentials` and picked up automatically.

**Method 2 — Environment variables**

Copy `.env.example` to `.env` and fill in:
```
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
```
Find these in the AWS Console under your account → **Security credentials** → **Access keys**.

**Method 3 — IAM Role (EC2 / ECS / Lambda)**

If running on an AWS compute resource with an IAM role attached, no credentials are needed — they are resolved automatically.

**Step 3 — Configure the tool to use Bedrock**

In `config.yaml`, set:
```yaml
provider: "bedrock"
aws_region: "us-east-1"   # change to your preferred region
model: "claude-opus-4-6"  # friendly name — mapped to Bedrock ID automatically
```

**Step 4 — Verify your Bedrock access**

```bash
aws sts get-caller-identity                         # confirms credentials work
aws bedrock list-foundation-models \
  --region us-east-1 \
  --by-provider anthropic \
  --query "modelSummaries[*].modelId"               # lists available Claude models
```

---

### 4. Configure your PST path

Edit `config.yaml` and set `pst_path` to the location of your `.pst` file:

```yaml
pst_path: "C:\\Users\\you\\Documents\\Outlook Files\\archive.pst"
```

---

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

---

## Cost Estimate

### Option A — Direct API

| Model | ~85k emails | Quality |
|---|---|---|
| `claude-opus-4-6` (default) | ~$300–350 | Highest |
| `claude-sonnet-4-6` | ~$70–90 | Best |
| `claude-haiku-4-5-20251001` | ~$6–9 | Good |

### Option B — AWS Bedrock

Same models, billed to your AWS account. Bedrock pricing is comparable to the direct API.
See [aws.amazon.com/bedrock/pricing](https://aws.amazon.com/bedrock/pricing/) for current rates.

Run `--test 200` first to verify results before committing to a full run.

---

## Output

Results are written to the `output/` directory:

- `resume_extraction.txt` — human-readable report with projects, skills, achievements, responsibilities, and collaborations
- `resume_extraction.json` — structured JSON for further processing

---

## Configuration

All settings live in `config.yaml`:

| Setting | Default | Description |
|---|---|---|
| `pst_path` | *(required)* | Path to your `.pst` file |
| `output_dir` | `output` | Where to write results |
| `provider` | `anthropic` | `anthropic` or `bedrock` |
| `aws_region` | `us-east-1` | AWS region (Bedrock only) |
| `role` | *(blank)* | Target role to tailor extraction toward |
| `model` | `claude-opus-4-6` | AI model to use |
| `batch_size` | `50` | Emails per API call |
| `max_body_chars` | `500` | Max email body length |
| `skip_folders` | see config | Folder names to ignore |

---

## Privacy

- Your `.env` (credentials) and `output/` (extracted email data) are excluded from git via `.gitignore`
- Your `.pst` file is never uploaded or transmitted — only short text excerpts are sent to the API for analysis
- When using Bedrock, all traffic stays within the AWS network
