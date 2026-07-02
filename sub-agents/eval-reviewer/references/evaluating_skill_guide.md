# Evaluating skill output quality

> How to test whether your skill produces good outputs using eval-driven iteration.

You wrote a skill, tried it on a prompt, and it seemed to work. But does it work reliably — across varied prompts, in edge cases, better than no skill at all? Running structured evaluations (evals) answers these questions and gives you a feedback loop for improving the skill systematically.

## Designing test cases

A test case has three parts:

* **Prompt**: a realistic user message — the kind of thing someone would actually type.
* **Expected output**: a human-readable description of what success looks like.
* **Input files** (optional): files the skill needs to work with.

Store test cases in `evals/evals.json` inside your skill directory:

```json
{
  "skill_name": "csv-analyzer",
  "evals": [
    {
      "id": 1,
      "prompt": "I have a CSV of monthly sales data in data/sales_2025.csv. Can you find the top 3 months by revenue and make a bar chart?",
      "expected_output": "A bar chart image showing the top 3 months by revenue, with labeled axes and values.",
      "files": ["evals/files/sales_2025.csv"]
    },
    {
      "id": 2,
      "prompt": "there's a csv in my downloads called customers.csv, some rows have missing emails — can you clean it up and tell me how many were missing?",
      "expected_output": "A cleaned CSV with missing emails handled, plus a count of how many were missing.",
      "files": ["evals/files/customers.csv"]
    }
  ]
}
```

**Tips for writing good test prompts:**

* **Start with 2-3 test cases.** Don't over-invest before you've seen your first round of results. You can expand the set later.
* **Vary the prompts.** Use different phrasings, levels of detail, and formality. Some prompts should be casual ("hey can you clean up this csv"), others precise ("Parse the CSV at data/input.csv, drop rows where column B is null, and write the result to data/output.csv").
* **Cover edge cases.** Include at least one prompt that tests a boundary condition — a malformed input, an unusual request, or a case where the skill's instructions might be ambiguous.
* **Use realistic context.** Real users mention file paths, column names, and personal context. Prompts like "process this data" are too vague to test anything useful.

Don't worry about defining specific pass/fail checks yet — just the prompts and expected outputs. You'll add detailed checks (called assertions) after you see what the first run produces.

## Running evals

The core pattern is to run each test case twice: once **with the skill** and once **without it** (or with a previous version). This gives you a baseline to compare against.

### Workspace structure

Organize eval results in a workspace directory alongside your skill directory. Each pass through the full eval loop gets its own `iteration-N/` directory. Within that, each test case gets an eval directory with `with_skill/` and `without_skill/` subdirectories:

```
csv-analyzer/
├── SKILL.md
└── evals/
    └── evals.json
csv-analyzer-workspace/
└── iteration-1/
    ├── eval-top-months-chart/
    │   ├── with_skill/
    │   │   ├── outputs/       # Files produced by the run
    │   │   ├── timing.json    # Tokens and duration
    │   │   └── grading.json   # Assertion results
    │   └── without_skill/
    │       ├── outputs/
    │       ├── timing.json
    │       └── grading.json
    ├── eval-clean-missing-emails/
    │   ├── with_skill/
    │   │   ├── outputs/
    │   │   ├── timing.json
    │   │   └── grading.json
    │   └── without_skill/
    │       ├── outputs/
    │       ├── timing.json
    │       └── grading.json
    └── benchmark.json         # Aggregated statistics
```

The main file you author by hand is `evals/evals.json`. The other JSON files (`grading.json`, `timing.json`, `benchmark.json`) are produced during the eval process — by the agent, by scripts, or by you.

### Spawning runs

Each eval run should start with a clean context — no leftover state from previous runs or from the skill development process. This ensures the agent follows only what the `SKILL.md` tells it. In environments that support subagents (Claude Code, for example), this isolation comes naturally: each child task starts fresh. Without subagents, use a separate session for each run.

For each run, provide:

* The skill path (or no skill for the baseline)
* The test prompt
* Any input files
* The output directory

Here's an example of the instructions you'd give the agent for a single with-skill run:

```
Execute this task:
- Skill path: /path/to/csv-analyzer
- Task: I have a CSV of monthly sales data in data/sales_2025.csv.
  Can you find the top 3 months by revenue and make a bar chart?
- Input files: evals/files/sales_2025.csv
- Save outputs to: csv-analyzer-workspace/iteration-1/eval-top-months-chart/with_skill/outputs/
```

For the baseline, use the same prompt but without the skill path, saving to `without_skill/outputs/`.

When improving an existing skill, use the previous version as your baseline. Snapshot it before editing (`cp -r <skill-path> <workspace>/skill-snapshot/`), point the baseline run at the snapshot, and save to `old_skill/outputs/` instead of `without_skill/`.

### Capturing timing data

Timing data lets you compare how much time and tokens the skill costs relative to the baseline — a skill that dramatically improves output quality but triples token usage is a different trade-off than one that's both better and cheaper. When each run completes, record the token count and duration:

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.332,
  "executor_start_time": "2026-01-15T10:30:00Z",
  "executor_end_time": "2026-01-15T10:30:00Z"
}
```

## Writing assertions

Assertions are verifiable statements about what the output should contain or achieve. Add them after you see your first round of outputs — you often don't know what "good" looks like until the skill has run.

Good assertions:

* `"The output file is valid JSON"` — programmatically verifiable.
* `"The bar chart has labeled axes"` — specific and observable.
* `"The report includes at least 3 recommendations"` — countable.

Weak assertions:

* `"The output is good"` — too vague to grade.
* `"The output uses exactly the phrase 'Total Revenue: $X'"` — too brittle; correct output with different wording would fail.

Not everything needs an assertion. Some qualities — writing style, visual design, whether the output "feels right" — are hard to decompose into pass/fail checks. These are better caught during human review. Reserve assertions for things that can be checked objectively.

Add assertions to each test case in `evals/evals.json`:

```json 
{
  "skill_name": "csv-analyzer",
  "evals": [
    {
      "id": 1,
      "prompt": "I have a CSV of monthly sales data in data/sales_2025.csv. Can you find the top 3 months by revenue and make a bar chart?",
      "expected_output": "A bar chart image showing the top 3 months by revenue, with labeled axes and values.",
      "files": ["evals/files/sales_2025.csv"],
      "assertions": [
        "The output includes a bar chart image file",
        "The chart shows exactly 3 months",
        "Both axes are labeled",
        "The chart title or caption mentions revenue"
      ]
    }
  ]
}
```

## Grading outputs

Grading means evaluating each assertion against the actual outputs and recording **PASS** or **FAIL** with specific evidence. The evidence should quote or reference the output, not just state an opinion.

The simplest approach is to give the outputs and assertions to an LLM and ask it to evaluate each one. For assertions that can be checked by code (valid JSON, correct row count, file exists with expected dimensions), use a verification script — scripts are more reliable than LLM judgment for mechanical checks and reusable across iterations.

```json
{
  "assertion_results": [
    {
      "text": "The output includes a bar chart image file",
      "passed": true,
      "evidence": "Found chart.png (45KB) in outputs directory"
    },
    {
      "text": "The chart shows exactly 3 months",
      "passed": true,
      "evidence": "Chart displays bars for March, July, and November"
    },
    {
      "text": "Both axes are labeled",
      "passed": false,
      "evidence": "Y-axis is labeled 'Revenue ($)' but X-axis has no label"
    },
    {
      "text": "The chart title or caption mentions revenue",
      "passed": true,
      "evidence": "Chart title reads 'Top 3 Months by Revenue'"
    }
  ],
  "summary": {
    "passed": 3,
    "failed": 1,
    "total": 4,
    "pass_rate": 0.75
  }
}
```

### Grading principles

* **Require concrete evidence for a PASS.** Don't give the benefit of the doubt. If an assertion says "includes a summary" and the output has a section titled "Summary" with one vague sentence, that's a FAIL — the label is there but the substance isn't.
* **Review the assertions themselves, not just the results.** While grading, notice when assertions are too easy (always pass regardless of skill quality), too hard (always fail even when the output is good), or unverifiable (can't be checked from the output alone). Fix these for the next iteration.

For comparing two skill versions, try **blind comparison**: present both outputs to an LLM judge without revealing which came from which version. The judge scores holistic qualities — organization, formatting, usability, polish — on its own rubric, free from bias about which version "should" be better. This complements assertion grading: two outputs might both pass all assertions but differ significantly in overall quality.

## Aggregating results

Once every run in the iteration is graded, compute summary statistics per configuration and save them to `benchmark.json` alongside the eval directories (e.g., `csv-analyzer-workspace/iteration-1/benchmark.json`):

```json 
{
  "metadata": {
    "eval_id": 2,
    "skill_name": "pdf",
    "skill_path": "/path/to/pdf",
    "executor_model": "claude-sonnet-4-20250514",
    "analyzer_model": "most-capable-model",
    "timestamp": "2026-01-15T10:30:00Z",
    "evals_run": [1, 2],
    "runs_per_configuration": 2
  },
"tool_metrics":{
      "tool_calls": {
        "Read": 5,
        "Write": 2,
        "Bash": 8,
        "Edit": 1,
        "Glob": 2,
        "Grep": 0
      },
      "total_tool_calls": 18,
      "total_steps": 6,
      "files_created": ["filled_form.pdf", "field_values.json"],
      "errors_encountered": 0,
      "output_chars": 12450,
      "transcript_chars": 3200
    },
"run_summary": {
    "with_skill": {
      "pass_rate": { "mean": 0.83, "stddev": 0.06 },
      "time_seconds": { "mean": 45.0, "stddev": 12.0 },
      "tokens": { "mean": 3800, "stddev": 400 }
    },
    "without_skill": {
      "pass_rate": { "mean": 0.33, "stddev": 0.10 },
      "time_seconds": { "mean": 32.0, "stddev": 8.0 },
      "tokens": { "mean": 2100, "stddev": 300 }
    },
    "delta": {
      "pass_rate": 0.50,
      "time_seconds": 13.0,
      "tokens": 1700
    }
  },
"notes": [
    "reggression patterns identified",
    "need more test cases to validate",
    "fragile assertions.", 
    "Eval {id} shows high variance (50% ± 40%) - may be flaky or model-dependent",
    "High tool usage"
    ]
}
```
### Metadata
The `metadata` field provides context about the evaluation run. It includes information such as the eval ID, skill name, skill path, executor model, analyzer model, timestamp, evals run, and runs per configuration.

**Fields:**

* `eval_id`: The ID of the evaluation run
* `skill_name`: The name of the skill being evaluated
* `skill_path`: The path to the skill being evaluated
* `executor_model`: The model used to execute the skill
* `analyzer_model`: The model used to analyze the skill
* `timestamp`: The timestamp of the evaluation run
* `evals_run`: List of eval IDs run in this iteration
* `runs_per_configuration`: Number of runs per configuration

### Tool Metrics
The `tool_metrics` field provides insights into how the model interacts with tools during the execution of the skill. It includes information about the types and frequency of tool calls, as well as metrics related to the overall execution of the skill.

**Fields:**

* `tool_calls`: Count per tool type
* `total_tool_calls`: Sum of all tool calls
* `total_steps`: Number of major execution steps
* `files_created`: List of output files created
* `errors_encountered: Number of errors during execution
* `output_chars`: Total character count of output files
* `transcript_chars`: Character count of transcript

### Run Summary
The `run_summary` field provides a high-level overview of the evaluation results. It includes the pass rate, time in seconds, and tokens used for both the "with skill" and "without skill" configurations. The `delta` field shows the difference between the two configurations, highlighting the impact of the skill on the evaluation results.

**Fields:**

* `with_skill`: Metrics for the "with skill" configuration
* `without_skill`: Metrics for the "without skill" configuration
* `delta`: Difference between the "with skill" and "without skill" configurations

### Delta Metrics
The `delta` tells you what the skill costs (more time, more tokens) and what it buys (higher pass rate). A skill that adds 13 seconds but improves pass rate by 50 percentage points is probably worth it. A skill that doubles token usage for a 2-point improvement might not be.

- **Mean** (`mean`): The average value of the metric across all runs in the iteration.
- **Standard deviation** (`stddev`): The amount of variation or dispersion of the metric across all runs in the iteration. A low standard deviation indicates that the metric is consistent across all runs, while a high standard deviation indicates that the metric varies significantly across runs.

**Note**: Standard deviation (`stddev`) is only meaningful with multiple runs per eval. In early iterations with just 2-3 test cases and single runs, focus on the raw pass counts and the delta — the statistical measures become useful as you expand the test set and run each eval multiple times.

### Notes 
This is a list of notes about the evaluation run. They can be used to provide additional context or information about the evaluation run. It can assits skill scalling and improvements, but the recoimendations orv feedback should be provided in a different place (see **Reviewing results with a human** section ). Common notes might include:

- **Skill failures** : Any issues or errors encountered during the execution of the skill.
- **Execution time** : The time it took to execute the skill.
- **Token usage** : The number of tokens used by the skill.
- **Memory usage** : The amount of memory used by the skill.
- **Output quality** : The quality of the output generated by the skill.
- **Error handling** : How the skill handles errors and exceptions.

---

## Analyzing patterns

Aggregate statistics can hide important patterns. After computing the benchmarks:

* **Remove or replace assertions that always pass in both configurations.** These don't tell you anything useful — the model handles them fine without the skill. They inflate the with-skill pass rate without reflecting actual skill value.
* **Investigate assertions that always fail in both configurations.** Either the assertion is broken (asking for something the model can't do), the test case is too hard, or the assertion is checking for the wrong thing. Fix these before the next iteration.
* **Study assertions that pass with the skill but fail without.** This is where the skill is clearly adding value. Understand *why* — which instructions or scripts made the difference?
* **Tighten instructions when results are inconsistent across runs.** If the same eval passes sometimes and fails others (reflected as high `stddev` in the benchmark), the eval may be flaky (sensitive to model randomness), or the skill's instructions may be ambiguous enough that the model interprets them differently each time. Add examples or more specific guidance to reduce ambiguity.
* **Check time and token outliers.** If one eval takes 3x longer than the others, read its execution transcript (the full log of what the model did during the run) to find the bottleneck.

## Reviewing results with a human

Assertion grading and pattern analysis catch a lot, but they only check what you thought to write assertions for. A human reviewer brings a fresh perspective — catching issues you didn't anticipate, noticing when the output is technically correct but misses the point, or spotting problems that are hard to express as pass/fail checks. For each test case, review the actual outputs alongside the grades.

Record specific feedback for each test case and save it in the workspace (e.g., as a `feedback.json` alongside the eval directories):

```json 
{
  "eval-top-months-chart": "The chart is missing axis labels and the months are in alphabetical order instead of chronological.",
  "eval-clean-missing-emails": ""
}
```

"The chart is missing axis labels" is actionable; "looks bad" is not. Empty feedback means the output looked fine — that test case passed your review. During the iteration step, focus your improvements on the test cases where you had specific complaints.

## Iterating on the skill

After grading and reviewing, you have three sources of signal:

* **Failed assertions** point to specific gaps — a missing step, an unclear instruction, or a case the skill doesn't handle.
* **Human feedback** points to broader quality issues — the approach was wrong, the output was poorly structured, or the skill produced a technically correct but unhelpful result.
* **Execution transcripts** reveal *why* things went wrong. If the agent ignored an instruction, the instruction may be ambiguous. If the agent spent time on unproductive steps, those instructions may need to be simplified or removed.

The most effective way to turn these signals into skill improvements is to give all three — along with the current `SKILL.md` — to an LLM and ask it to propose changes. The LLM can synthesize patterns across failed assertions, reviewer complaints, and transcript behavior that would be tedious to connect manually. When prompting the LLM, include these guidelines:

* **Generalize from feedback.** The skill will be used across many different prompts, not just the test cases. Fixes should address underlying issues broadly rather than adding narrow patches for specific examples.
* **Keep the skill lean.** Fewer, better instructions often outperform exhaustive rules. If transcripts show wasted work (unnecessary validation, unneeded intermediate outputs), remove those instructions. If pass rates plateau despite adding more rules, the skill may be over-constrained — try removing instructions and see if results hold or improve.
* **Explain the why.** Reasoning-based instructions ("Do X because Y tends to cause Z") work better than rigid directives ("ALWAYS do X, NEVER do Y"). Models follow instructions more reliably when they understand the purpose.
* **Bundle repeated work.** If every test run independently wrote a similar helper script (a chart builder, a data parser), that's a signal to bundle the script into the skill's `scripts/` directory. 

### The loop

1. Give the eval signals and current `SKILL.md` to an LLM and ask it to propose improvements.
2. Review and apply the changes.
3. Rerun all test cases in a new `iteration-<N+1>/` directory.
4. Grade and aggregate the new results.
5. Review with a human. Repeat.

Stop when you're satisfied with the results, feedback is consistently empty, or you're no longer seeing meaningful improvement between iterations.

