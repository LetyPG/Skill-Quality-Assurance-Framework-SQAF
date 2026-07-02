# Specification

The complete format specification for Agent Skills.

## Directory structure

A skill is a directory containing, at minimum, a `SKILL.md` file:

```
skill-name/
├── SKILL.md          # Required: metadata + instructions
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
├── assets/           # Optional: templates, resources
└── ...               # Any additional files or directories
```

## `SKILL.md` format

The `SKILL.md` file must contain YAML frontmatter followed by Markdown content.

### Frontmatter

| Field           | Required | Constraints                                                                                                       |
| --------------- | -------- | ----------------------------------------------------------------------------------------------------------------- |
| `name`          | Yes      | Max 64 characters. Lowercase letters, numbers, and hyphens only. Must not start or end with a hyphen.             |
| `description`   | Yes      | Max 1024 characters. Non-empty. Describes what the skill does and when to use it.                                 |
| `license`       | No       | License name or reference to a bundled license file.                                                              |
| `compatibility` | No       | Max 500 characters. Indicates environment requirements (intended product, system packages, network access, etc.). |
| `metadata`      | No       | Arbitrary key-value mapping for additional metadata.                                                              |
| `allowed-tools` | No       | Space-separated string of pre-approved tools the skill may use. (Experimental)                                    |

  **Minimal example:**

  ```yaml
  ---
  name: skill-name
  description: A description of what this skill does and when to use it.
  ---
  ```

  **Example with optional fields:**

  ```yaml
  ---
  name: pdf-processing
  description: Extract PDF text, fill forms, merge files. Use when handling PDFs.
  license: Apache-2.0
  metadata:
    author: example-org
    version: "1.0"
  ---
  ```

#### `name` field

The required `name` field:

* Must be 1-64 characters
* May only contain unicode lowercase alphanumeric characters (`a-z`, `0-9`) and hyphens (`-`)
* Must not start or end with a hyphen (`-`)
* Must not contain consecutive hyphens (`--`)
* Must match the parent directory name

  **Valid examples:**

  ```yaml theme={null}
  name: pdf-processing
  ```

  ```yaml theme={null}
  name: data-analysis
  ```

  ```yaml theme={null}
  name: code-review
  ```

  **Invalid examples:**

  ```yaml theme={null}
  name: PDF-Processing  # uppercase not allowed
  ```

  ```yaml theme={null}
  name: -pdf  # cannot start with hyphen
  ```

  ```yaml theme={null}
  name: pdf--processing  # consecutive hyphens not allowed
  ```

#### `description` field

The required `description` field:

* Must be 1-1024 characters
* Should describe both what the skill does and when to use it
* Should include specific keywords that help agents identify relevant tasks

  **Good example:**

  ```yaml
  description: Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction.
  ```

  **Poor example:**

  ```yaml theme={null}
  description: Helps with PDFs.
  ```

#### `license` field

The optional `license` field:

* Specifies the license applied to the skill
* We recommend keeping it short (either the name of a license or the name of a bundled license file)

  **Example:**

  ```yaml theme={null}
  license: Proprietary. LICENSE.txt has complete terms
  ```

#### `compatibility` field

The optional `compatibility` field:

* Must be 1-500 characters if provided
* Should only be included if your skill has specific environment requirements
* Can indicate intended product, required system packages, network access needs, etc.

  **Examples:**

  ```yaml
  compatibility: Designed for Claude Code (or similar products)
  ```

  ```yaml
  compatibility: Requires git, docker, jq, and access to the internet
  ```

  ```yaml
  compatibility: Requires Python 3.14+ and uv
  ```

**Note:** Most skills do not need the `compatibility` field.


#### `metadata` field

The optional `metadata` field:

* A map from string keys to string values
* Clients can use this to store additional properties not defined by the Agent Skills spec
* We recommend making your key names reasonably unique to avoid accidental conflicts

  **Example:**

  ```yaml theme={null}
  metadata:
    author: example-org
    version: "1.0"
  ```

#### `allowed-tools` field

The optional `allowed-tools` field:

* A space-separated string of tools that are pre-approved to run
* Experimental. Support for this field may vary between agent implementations

  **Example:**

  ```yaml theme={null}
  allowed-tools: Bash(git:*) Bash(jq:*) Read
  ```

### Body content

The Markdown body after the frontmatter contains the skill instructions. There are no format restrictions. Write whatever helps agents perform the task effectively.

Recommended sections:

* Step-by-step instructions
* Examples of inputs and outputs
* Common edge cases

Note that the agent will load this entire file once it's decided to activate a skill. Consider splitting longer `SKILL.md` content into referenced files.

---

## Best Practices fpr Skill Implementation

### Design coherent units

Deciding what a skill should cover is like deciding what a function should do: you want it to encapsulate a coherent unit of work that composes well with other skills. Skills scoped too narrowly force multiple skills to load for a single task, risking overhead and conflicting instructions. Skills scoped too broadly become hard to activate precisely. A skill for querying a database and formatting the results may be one coherent unit, while a skill that also covers database administration is probably trying to do too much.

### Aim for moderate detail

Overly comprehensive skills can hurt more than they help — the agent struggles to extract what's relevant and may pursue unproductive paths triggered by instructions that don't apply to the current task. Concise, stepwise guidance with a working example tends to outperform exhaustive documentation. When you find yourself covering every edge case, consider whether most are better handled by the agent's own judgment.

### Structure large skills with progressive disclosure

The specification recommends keeping `SKILL.md` under 500 lines and 5,000 tokens — just the core instructions the agent needs on every run. When a skill legitimately needs more content, move detailed reference material to separate files in `references/` or similar directories.

The key is telling the agent *when* to load each file. "Read `references/api-errors.md` if the API returns a non-200 status code" is more useful than a generic "see references/ for details." This lets the agent load context on demand rather than up front, which is how progressive disclosure is designed to work.
