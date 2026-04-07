# Loophole

**Adversarial moral-legal code system** — an AI tool that stress-tests your ethical principles by trying to break them.

## The Idea

Real legal systems evolve slowly. A law gets written, someone finds a loophole, a court patches it, someone finds another loophole. This process takes decades. Loophole compresses it into minutes.

You state your moral principles in plain language. An AI legislator drafts a formal legal code from them. Then two adversarial agents attack it:

- **The Loophole Finder** searches for scenarios that are *technically legal* under your code but *morally wrong* according to your principles. Think creative rule-lawyering, exploiting vague definitions, finding gaps the drafters didn't anticipate.

- **The Overreach Finder** searches for the opposite: scenarios your code *prohibits* that you'd actually consider *morally acceptable*. Good Samaritan situations, overbroad rules that catch innocent behavior, emergencies where rigid compliance causes worse outcomes.

When an attack lands, a **Judge agent** tries to patch the code automatically — but only if the fix doesn't break any previous ruling. Every resolved case becomes a permanent constraint, a growing test suite the code must satisfy.

If the Judge can't find a consistent fix — meaning any patch would contradict a prior decision — the case gets **escalated to you**. These escalated cases are guaranteed to be interesting: they represent genuine tensions in your own moral framework, places where your principles actually conflict with each other.

The legal code gets progressively more robust. But the real output isn't the code — it's what you discover about your own beliefs.

## How It Works

```
                    +-----------------+
                    |  Your Moral     |
                    |  Principles     |
                    +--------+--------+
                             |
                             v
                    +--------+--------+
                    |   Legislator    |
                    | (drafts legal   |
                    |  code from      |
                    |  principles)    |
                    +--------+--------+
                             |
                             v
              +--------------+--------------+
              |                             |
    +---------v----------+      +-----------v--------+
    |  Loophole Finder   |      |  Overreach Finder  |
    |  (legal but        |      |  (illegal but      |
    |   immoral)         |      |   moral)           |
    +--------+-----------+      +-----------+--------+
              |                             |
              +-------------+---------------+
                            |
                            v
                   +--------+--------+
                   |     Judge       |
                   | (auto-resolve   |
                   |  or escalate)   |
                   +--------+--------+
                            |
                +-----------+-----------+
                |                       |
        +-------v-------+      +-------v--------+
        | Auto-resolved |      |  Escalated     |
        | (code updated,|      |  to YOU        |
        |  case becomes |      |  (genuine      |
        |  precedent)   |      |   moral        |
        +---------------+      |   dilemma)     |
                               +----------------+
```

Each resolved case — whether by the Judge or by you — becomes binding precedent. The adversarial agents attack again, and the cycle repeats. Round after round, the legal code tightens, and the cases that reach you get harder and more revealing.

## Setup

Requires Python 3.12+.

```bash
# Clone and install
git clone <repo-url>
cd law
uv sync

# If using Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Run With Anthropic

Use the default config as-is:

```yaml
model:
  provider: "anthropic"
  default: "claude-sonnet-4-20250514"
  max_tokens: 4096
  base_url: null
  api_key_env: "ANTHROPIC_API_KEY"
```

### Run With Ollama

The repo now supports a local Ollama server without changing any agent code.

```bash
ollama pull llama3.1:8b
ollama serve
```

Then update `config.yaml`:

```yaml
model:
  provider: "ollama"
  default: "llama3.1:8b"
  max_tokens: 4096
  base_url: "http://localhost:11434"
  api_key_env: null
```

### Run With Another Local OpenAI-Compatible Server

LM Studio, vLLM, llama.cpp server, and similar tools usually expose a `/v1/chat/completions` endpoint.

```yaml
model:
  provider: "openai-compatible"
  default: "local-model-name"
  max_tokens: 4096
  base_url: "http://localhost:1234/v1"
  api_key_env: "OPENAI_API_KEY"
```

If your local server does not require auth, set `api_key_env: null`.

### Recommended Local Setup

For smaller local machines, start with a conservative configuration and a strong instruct model rather than a larger reasoning model.

Current recommended baseline:

```yaml
model:
  provider: "openai-compatible"
  default: "qwen2.5-7b-instruct"
  max_tokens: 4096
  base_url: "http://localhost:1234/v1"
  api_key_env: null

temperatures:
  legislator: 0.4
  loophole_finder: 0.9
  overreach_finder: 0.9
  judge: 0.2

loop:
  max_rounds: 3
  cases_per_agent: 1
```

Why these defaults:
- `qwen2.5-7b-instruct` is a better fit for structured prompt-following than smaller chat models or larger reasoning models on modest hardware.
- `judge: 0.2` reduces format drift and makes validation more stable.
- `max_rounds: 3` and `cases_per_agent: 1` keep first-run latency manageable while testing a local setup.

For LM Studio specifically:
1. Load the model in LM Studio.
2. Start the local server.
3. Make sure the OpenAI-compatible endpoint is available at `http://localhost:1234/v1`.
4. Run Loophole normally.

## Usage

### Start a new session

Interactive mode:
```bash
uv run python -m loophole.main
```

Or directly with a domain and principles file:
```bash
uv run python -m loophole.main new --domain privacy -p examples/privacy_principles.txt
```

You'll see the initial legal code, then the adversarial loop begins. Each round:
1. Both adversarial agents attack the current code
2. The Judge processes each case (auto-resolve or escalate)
3. You see a summary and choose to continue, view the code, or stop

When a case is escalated, you'll be prompted to make a decision. Your decision becomes a new constraint that the legal code must respect going forward.

### Resume a session

Sessions auto-save after every case. Pick up where you left off:
```bash
uv run python -m loophole.main resume
```

### Generate a visualization

After a session (or for any past session), generate an HTML report:
```bash
uv run python -m loophole.main visualize
```

This creates a `report.html` in the session directory with:
- Your moral principles and the initial legal code
- A timeline of every adversarial case
- Git-style diffs showing how the code changed after each case
- The final legal code

### List sessions

```bash
uv run python -m loophole.main list
```

## Configuration

Edit `config.yaml` to tune the system:

```yaml
model:
  provider: "anthropic"                 # anthropic | ollama | openai-compatible
  default: "claude-sonnet-4-20250514"   # Model name for the selected provider
  max_tokens: 4096
  base_url: null                         # Required for ollama or openai-compatible
  api_key_env: "ANTHROPIC_API_KEY"      # Optional env var name for provider auth

temperatures:
  legislator: 0.4          # Lower = more precise drafting
  loophole_finder: 0.9     # Higher = more creative attacks
  overreach_finder: 0.9
  judge: 0.2               # Lower = more conservative judgments

loop:
  max_rounds: 3
  cases_per_agent: 1       # How many cases each attacker finds per round

session_dir: "sessions"
```

## Writing Good Principles

The system works best when your principles are:

- **Specific enough to draft from.** "I believe in fairness" is too vague. "Companies should not sell user data without explicit, informed consent" gives the legislator something to work with.
- **Broad enough to have tensions.** If your principles only cover one narrow situation, the adversarial agents won't find interesting cases. Cover the domain from multiple angles.
- **Honest.** The system surfaces conflicts in *your* beliefs. If you state principles you don't actually hold, the escalated cases won't be meaningful.

See `examples/privacy_principles.txt` for a starting point.

## Project Structure

```
loophole/
  main.py              CLI and main adversarial loop
  models.py            Data models (SessionState, Case, LegalCode)
  llm.py               Provider-aware LLM client (Anthropic or local backends)
  parsing.py           Tolerant output parsing and repair helpers for local models
  prompts.py           All agent prompt templates
  session.py           Session persistence (JSON + markdown)
  visualize.py         HTML report generator
  agents/
    base.py            Base agent class
    legislator.py      Drafts and revises the legal code
    loophole_finder.py Finds legal-but-immoral scenarios
    overreach_finder.py Finds illegal-but-moral scenarios
    judge.py           Auto-resolves cases or escalates

sessions/              One directory per session (auto-created)
examples/              Example moral principles files
config.yaml            Model and loop configuration
```

## Why This Matters

Most attempts to formalize ethics start with the rules and hope they cover everything. Loophole starts with your intuitions and systematically finds where they break down. It's less "solve ethics" and more "discover what you actually believe by watching it fail."

The same architecture applies anywhere humans write rules for AI systems: content moderation policies, LLM system prompts, codes of conduct, safety specifications. Anywhere there's a gap between what the rules say and what the rules mean, Loophole will find it.

## Local Model Reliability

Hosted frontier models are usually better at returning exact tagged output. Smaller local models are more likely to add preambles, code fences, partial tags, or slightly malformed structures.

Loophole now hardens this path in two ways:
- It uses more tolerant parsing for tags like `<legal_code>`, `<verdict>`, `<passes>`, `<description>`, and `<explanation>`.
- If parsing fails, it performs one low-temperature repair pass that asks the model to re-emit the same content in the exact expected format.

This does not make the model smarter. It makes the system less brittle when the model mostly follows instructions but misses the exact output shape.
