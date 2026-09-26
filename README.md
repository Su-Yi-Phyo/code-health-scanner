# ⚡ CodePulse

**AI-Powered Code Health Scanner with IBM Bob**

CodePulse analyzes public GitHub repositories, identifies risky Python files, detects maintainability issues such as duplicate and dead code, ranks files by risk, and uses **IBM Bob** to generate AI-powered explanations that help developers understand why a piece of code may be problematic.

🌐 **Live Demo:** https://codepulse-nu-three.vercel.app

---

## 🎯 Problem

As software projects grow, codebases become increasingly difficult to understand and maintain.

Developers may encounter:

- Duplicated logic
- Dead or unused code
- Large or risky files
- Maintainability issues spread across the repository
- Static-analysis results that are difficult to interpret
- Difficulty deciding which files should be reviewed first

Traditional static-analysis tools can identify problems, but developers still need to interpret those findings and determine where to focus their attention.

**CodePulse turns repository analysis into an understandable and prioritized code-health report.**

---

## 💡 Solution

CodePulse combines **static code analysis, risk scoring, and AI-assisted explanation** in one developer-friendly workflow.

A user simply provides a public GitHub repository URL.

CodePulse then:

1. Retrieves and scans the repository.
2. Identifies supported Python source files.
3. Performs static code analysis.
4. Detects duplicate code and potential dead code.
5. Calculates code-health risk scores.
6. Prioritizes files that deserve attention.
7. Displays repository-level and file-level findings in a visual dashboard.
8. Uses **IBM Bob** to explain selected code and detected concerns in developer-friendly language.

Instead of only telling developers that something is wrong, CodePulse helps them understand **where to look and why it matters**.

---

## ✨ Key Features

### 🔍 Repository Analysis

Analyze a public GitHub repository directly from its URL without manually uploading source files.

### 📊 Code Health Overview

Get a high-level overview of the analyzed repository and quickly understand its overall code-health status.

### ⚠️ Risk-Based Prioritization

CodePulse calculates risk information for analyzed files and helps developers identify which files deserve attention first.

### ♻️ Duplicate Code Detection

Detect duplicated code patterns that may increase maintenance effort and make future changes more difficult.

### 🧹 Dead Code Detection

Identify potentially unused definitions and unnecessary code that may increase codebase complexity.

### 📁 Repository Explorer

Browse analyzed files, inspect their individual risk information, and review detected issues.

### 🤖 IBM Bob Explanations

Request an AI-generated explanation for a selected file.

IBM Bob receives relevant code context and scanner findings and returns concise code-health observations to help developers understand the detected concerns.

---

## 🤖 IBM Bob Integration

IBM Bob is the AI reasoning layer behind CodePulse's code-explanation capability.

Static analysis is useful for identifying measurable problems, but its output alone may not explain the meaning of those findings clearly.

CodePulse combines deterministic analysis with IBM Bob:

```text
GitHub Repository
        ↓
Static Code Analysis
        ↓
Issue Detection
        ↓
Risk Scoring
        ↓
IBM Bob
        ↓
Developer-Friendly Explanation