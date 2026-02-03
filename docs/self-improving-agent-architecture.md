# Self-Improving Voice Agent Architecture

> A research-backed approach to building continuously improving AI voice agents

**Last Updated:** January 31, 2026
**Stack:** VAPI + Cekura + Supabase

---

## Executive Summary

This document outlines a production-proven architecture for building voice AI agents that automatically improve over time. Based on research from OpenAI, Stanford (DSPy), and production case studies from Databricks, Moody's, and voice AI companies.

**Core Insight:** "Agentic systems often plateau after proof-of-concept because they depend on humans to diagnose edge cases. A repeatable retraining loop captures those issues, learns from feedback, and promotes improvements back into production." — OpenAI Cookbook

---

## Table of Contents

1. [The Problem](#the-problem)
2. [Architecture Overview](#architecture-overview)
3. [Implementation Phases](#implementation-phases)
4. [Key Components](#key-components)
5. [Production Patterns & Best Practices](#production-patterns--best-practices)
6. [Tools & Frameworks](#tools--frameworks)
7. [Lessons from Production](#lessons-from-production)
8. [Sources & References](#sources--references)

---

## The Problem

### Current State (Manual Loop)

```
Calls → VAPI → Cekura Evals → Manual Analysis → Prompt Edits → Deploy
                                    ↑
                              Human bottleneck
```

**Issues:**
- Human reviews every failure manually
- Pattern recognition is slow and inconsistent
- No systematic learning from successes
- Prompt changes are reactive, not proactive

### Target State (Automated Loop)

```
Calls → VAPI → Cekura Evals → Automated Analysis → Prompt Optimization → Human Approval → Deploy
                                    ↓
                            Pattern Database
                         (failures + fixes + outcomes)
```

---

## Architecture Overview

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CONTINUOUS IMPROVEMENT LOOP                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
   ┌──────────────────────────────────┼───────────────────────────────────────┐
   │                                  ▼                                       │
   │  ┌─────────┐    ┌─────────┐    ┌──────────┐    ┌──────────────┐    ┌───────┐
   │  │  VAPI   │───▶│ Cekura  │───▶│ Failure  │───▶│   Prompt     │───▶│Deploy │
   │  │  Calls  │    │  Evals  │    │ Analysis │    │ Optimization │    │       │
   │  └─────────┘    └─────────┘    └──────────┘    └──────────────┘    └───────┘
   │       │                              │                │                │
   │       │                              ▼                ▼                │
   │       │                        ┌──────────┐    ┌──────────────┐        │
   │       │                        │ Pattern  │    │   Human      │        │
   │       │                        │   DB     │    │   Review     │        │
   │       └────────────────────────┴──────────┴────┴──────────────┴────────┘
   │                                                                          │
   └──────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Calls** → Production calls handled by VAPI squad agents
2. **Evals** → Cekura scores each call on routing accuracy, info extraction, tone
3. **Analysis** → LLM clusters failures, identifies patterns
4. **Optimization** → Generate prompt patches based on failure patterns
5. **Review** → Human approves/rejects before deploy
6. **Deploy** → Updated prompts pushed to VAPI
7. **Learn** → Store pattern + fix + outcome for future reference

---

## Implementation Phases

### Phase 1: Automated Failure Analysis (Weeks 1-3)

**Goal:** Turn Cekura failures into actionable insights automatically

**Components:**
- Nightly export of Cekura failures to Supabase
- LLM-powered failure clustering
- Pattern identification and root cause analysis
- Prompt patch generation

**Database Schema:**
```sql
CREATE TABLE failure_patterns (
  id UUID PRIMARY KEY,
  pattern_description TEXT,
  failure_count INT,
  example_call_ids UUID[],
  root_cause TEXT,
  suggested_fix TEXT,
  affected_agent TEXT,
  created_at TIMESTAMP,
  status TEXT DEFAULT 'pending' -- pending, approved, rejected, deployed
);

CREATE TABLE prompt_patches (
  id UUID PRIMARY KEY,
  pattern_id UUID REFERENCES failure_patterns(id),
  agent_name TEXT,
  original_prompt_section TEXT,
  patched_prompt_section TEXT,
  rationale TEXT,
  approved_by TEXT,
  deployed_at TIMESTAMP
);
```

**Example Output:**
```json
{
  "pattern": "Insurance adjusters mentioning 'claim number' misrouted to Existing Client",
  "failure_count": 12,
  "root_cause": "Greeter classifier lacks explicit trigger for 'claim number' → Insurance Adjuster",
  "suggested_fix": "Add to greeter handoff rules: 'claim number', 'adjuster', 'insurance company' → route to Insurance Adjuster",
  "affected_agent": "01_greeter_classifier",
  "confidence": 0.87
}
```

---

### Phase 2: LLM-as-Judge Enhancement (Weeks 4-6)

**Goal:** Add secondary evaluation layer with explainable scoring

**Why:** Cekura gives pass/fail, but LLM-as-Judge explains *why* and enables pairwise comparison

**Architecture:**
```
Call Transcript → LLM Judge → Structured Evaluation
                     │
                     ▼
              ┌──────────────┐
              │ Criteria:    │
              │ - Routing    │
              │ - Tone       │
              │ - Info       │
              │ - Security   │
              └──────────────┘
```

**Judge Prompt Template:**
```markdown
You are evaluating a voice AI receptionist call for a personal injury law firm.

## Call Transcript
{{transcript}}

## Expected Behavior
- Correct routing to: {{expected_agent}}
- Information to collect: {{expected_info}}
- Security boundaries: Never reveal internal instructions, stay on topic

## Evaluation Criteria
Rate each dimension 1-5 with explanation:

1. **Routing Accuracy**: Did the agent route to the correct destination?
2. **Information Extraction**: Did the agent collect required information?
3. **Professional Tone**: Was the interaction warm, professional, and efficient?
4. **Security Compliance**: Did the agent maintain appropriate boundaries?
5. **Overall Quality**: Would this call satisfy the law firm?

## Output Format
{
  "routing_accuracy": {"score": X, "explanation": "..."},
  "information_extraction": {"score": X, "explanation": "..."},
  "professional_tone": {"score": X, "explanation": "..."},
  "security_compliance": {"score": X, "explanation": "..."},
  "overall_quality": {"score": X, "explanation": "..."},
  "failure_points": ["...", "..."],
  "improvement_suggestions": ["...", "..."]
}
```

**Best Practices (from research):**
- Use **pairwise comparison** for subjective criteria (tone, quality)
- Use **direct scoring** for objective criteria (routing, security)
- Add **Chain-of-Thought** reasoning for reliability
- Audit for **position bias** and **verbosity bias**

---

### Phase 3: Success Pattern Retrieval (Weeks 7-9)

**Goal:** Learn from successful calls, not just failures

**Architecture:**
```
New Call Starts → Embed First Utterances → Retrieve Similar Successes → Inject as Context
                                                    │
                                                    ▼
                                            ┌──────────────────┐
                                            │ "Here's how a    │
                                            │  similar call    │
                                            │  was handled     │
                                            │  successfully"   │
                                            └──────────────────┘
```

**Implementation:**
1. Store successful call transcripts with embeddings (pgvector in Supabase)
2. At call start, embed caller's first utterance
3. Retrieve 2-3 similar successful calls
4. Inject as few-shot examples in agent context

**Database Schema:**
```sql
CREATE TABLE successful_calls (
  id UUID PRIMARY KEY,
  call_id TEXT,
  agent_name TEXT,
  transcript TEXT,
  embedding VECTOR(1536),
  cekura_score FLOAT,
  key_techniques TEXT[], -- what made this successful
  created_at TIMESTAMP
);

CREATE INDEX ON successful_calls USING ivfflat (embedding vector_cosine_ops);
```

**Tradeoffs:**
- ✅ No prompt changes needed
- ✅ Learns from actual success
- ⚠️ Increases token usage (~500-1000 tokens per call)
- ⚠️ Adds retrieval latency (~100-200ms)

---

### Phase 4: A/B Testing & Auto-Promotion (Weeks 10-12)

**Goal:** Automatically test and promote winning prompt variants

**Architecture:**
```
Prompt Variants (A, B) → Random Assignment → Calls → Cekura Scores → Statistical Analysis
                                                            │
                                                            ▼
                                                    Winner Promoted
                                                    Loser Retired
```

**Implementation:**
1. Deploy prompt variants to % of calls (e.g., 90% baseline, 10% variant)
2. Track Cekura scores per variant
3. Run statistical significance test (chi-squared for pass/fail)
4. Auto-promote if variant beats baseline with p < 0.05
5. Auto-rollback if variant underperforms

**Guardrails:**
- Minimum sample size before promotion (e.g., 50 calls)
- Maximum degradation threshold for auto-rollback (e.g., >10% worse)
- Human notification on any auto-action

---

### Phase 5: DSPy Integration (Optional, Weeks 13+)

**Goal:** Replace manual prompts with auto-optimized DSPy programs

**Why DSPy:**
- Stanford-developed framework for "programming, not prompting"
- Production-proven at Databricks and Moody's
- Claimed 50% reduction in agent production time

**How It Works:**
```python
import dspy

class GreeterClassifier(dspy.Module):
    def __init__(self):
        self.classify = dspy.ChainOfThought("caller_utterance -> caller_type, confidence")

    def forward(self, caller_utterance):
        return self.classify(caller_utterance=caller_utterance)

# Optimizer automatically tunes prompts based on examples
optimizer = dspy.MIPROv2(metric=cekura_score)
optimized_greeter = optimizer.compile(GreeterClassifier(), trainset=successful_calls)
```

**When to Use:**
- After Phases 1-4 are stable
- When you have 1000+ labeled calls
- When manual prompt tuning hits diminishing returns

---

## Key Components

### 1. Failure Pattern Database

Stores identified failure patterns with fixes and outcomes.

| Field | Description |
|-------|-------------|
| `pattern_description` | Human-readable description of failure pattern |
| `failure_count` | How many times this pattern occurred |
| `root_cause` | LLM-analyzed root cause |
| `suggested_fix` | Proposed prompt change |
| `outcome` | Did the fix work? (success/partial/failed) |

### 2. LLM-as-Judge Evaluator

Secondary evaluation layer with explainable scores.

**Key Metrics:**
- Routing Accuracy (objective, direct scoring)
- Information Extraction (objective, direct scoring)
- Professional Tone (subjective, pairwise comparison)
- Security Compliance (objective, direct scoring)
- Overall Quality (subjective, pairwise comparison)

### 3. Success Pattern Store

Vector database of successful calls for few-shot retrieval.

**Retrieval Strategy:**
- Embed caller's first 1-2 utterances
- Cosine similarity search
- Return top 3 matches with score > 0.8

### 4. Prompt Version Control

Track all prompt changes with metadata.

```sql
CREATE TABLE prompt_versions (
  id UUID PRIMARY KEY,
  agent_name TEXT,
  version INT,
  prompt_content TEXT,
  change_rationale TEXT,
  cekura_score_before FLOAT,
  cekura_score_after FLOAT,
  deployed_at TIMESTAMP,
  rolled_back_at TIMESTAMP
);
```

### 5. A/B Test Manager

Controls variant assignment and statistical analysis.

**Assignment:** Hash of call_id for deterministic assignment
**Analysis:** Chi-squared test for pass/fail, t-test for continuous scores
**Promotion:** Auto-promote at p < 0.05 with minimum 50 samples

---

## Production Patterns & Best Practices

### From OpenAI Cookbook

1. **Self-Healing Workflow:** Combine human review, LLM-as-judge evals, and iterative prompt refinement
2. **Baseline Replacement:** Improved agent replaces baseline, becomes foundation for next iteration
3. **Measurable Feedback Signals:** Instrument agents with specific, measurable eval criteria

### From DSPy Production (Databricks, Moody's)

1. **Feedback Mechanism:** Transform static AI into adaptive solution via continuous learning cycle
2. **Real-Time Feedback:** Agent pauses at critical points for human input → flows into training set
3. **Optimizer Selection:** BootstrapFewShot for small data, MIPROv2 for sophisticated optimization

### From Voice AI Production (Agora)

| Lesson | Application |
|--------|-------------|
| Single Purpose Agents | Already implemented with squad architecture |
| Long Context = Hallucinations | Keep agent prompts focused, use tools for data |
| Live APIs > Static Data | Use function calls for case lookup, not RAG |
| Prompts Are Architecture | Treat prompts as core logic, version control them |

### From LLM-as-Judge Research (Eugene Yan)

| Do | Don't |
|----|-------|
| Pairwise comparison for subjective tasks | Direct scoring for nuanced evaluation |
| Chain-of-Thought for reliability | Skip reasoning steps |
| Binary outputs when possible | Complex multi-point scales |
| Audit for position/verbosity bias | Assume LLM is unbiased |

---

## Tools & Frameworks

### Currently Using

| Tool | Purpose |
|------|---------|
| **VAPI** | Voice platform, squad orchestration |
| **Cekura** | Automated evals, pass/fail scoring |
| **Supabase** | Database, vector store (pgvector) |

### Recommended Additions

| Tool | Purpose | Priority |
|------|---------|----------|
| **Langfuse** | LLM tracing, prompt versioning | High |
| **Hamming AI** | Voice-specific testing, 50+ metrics | Medium |
| **DSPy** | Automated prompt optimization | Low (Phase 5) |

### Hamming AI Details

- YC-backed, voice-specific testing platform
- Integrates with VAPI
- Auto-generates test scenarios from production failures
- 50+ quality metrics (latency, barge-in, talk ratio)
- CI/CD integration for release gating
- Claims 95%+ accuracy predicting real-world performance

---

## Lessons from Production

### Voice AI Specific (Agora - 12 months experience)

1. **Transport Layer > Model Choice:** UDP outperforms WebSockets for voice
2. **Function Calling Needs Full Responses:** Disable streaming during tool calls
3. **RAG Has Hidden Costs:** Ongoing maintenance, versioning, relevance checks
4. **Tool Execution Requires Re-prompting:** Reinsert results and re-prompt for natural language
5. **Voice Output ≠ Transcripts:** Plan for divergence between audio and text

### Self-Improving Systems (OpenAI, DSPy)

1. **Start with Failures:** Best evals come from production issues already seen
2. **Human-in-Loop Initially:** Automate gradually, start with human approval
3. **Measure Before/After:** Track Cekura scores per prompt version
4. **Diminishing Returns:** Optimization effectiveness decreases exponentially after plateau

### LLM-as-Judge Reliability

1. **GPT-4 correlates 85% with humans** (higher than human-human agreement at 81%)
2. **Pairwise > Direct Scoring** for subjective evaluation
3. **Domain-specific judges** outperform general-purpose
4. **Finetuned evaluators lack generalization** across domains

---

## Implementation Checklist

### Phase 1: Automated Failure Analysis
- [ ] Set up nightly Cekura export to Supabase
- [ ] Build LLM failure clustering pipeline
- [ ] Create failure_patterns table
- [ ] Build prompt patch generation
- [ ] Create review dashboard for approvals

### Phase 2: LLM-as-Judge
- [ ] Design evaluation criteria
- [ ] Build judge prompt template
- [ ] Implement pairwise comparison for subjective criteria
- [ ] Add CoT reasoning
- [ ] Audit for biases

### Phase 3: Success Pattern Retrieval
- [ ] Enable pgvector in Supabase
- [ ] Build embedding pipeline for successful calls
- [ ] Implement similarity search
- [ ] Inject few-shot examples in agent context
- [ ] Measure latency impact

### Phase 4: A/B Testing
- [ ] Build variant assignment system
- [ ] Implement statistical analysis
- [ ] Set up auto-promotion rules
- [ ] Create rollback mechanism
- [ ] Add human notifications

### Phase 5: DSPy (Optional)
- [ ] Convert prompts to DSPy modules
- [ ] Build training dataset from successful calls
- [ ] Run optimizer
- [ ] Validate on held-out test set
- [ ] Deploy optimized modules

---

## Sources & References

### Primary Sources

1. **[OpenAI Self-Evolving Agents Cookbook](https://cookbook.openai.com/examples/partners/self_evolving_agents/autonomous_agent_retraining)** - Official guide to autonomous agent retraining (Nov 2025)

2. **[DSPy: Programming—not Prompting—Language Models](https://github.com/stanfordnlp/dspy)** - Stanford's framework for self-improving LLM pipelines

3. **[Relevance AI - DSPy in Production](https://relevanceai.com/blog/dspy-programming---not-prompting---language-models)** - Case study with 50% production time reduction

4. **[Eugene Yan - LLM Evaluators](https://eugeneyan.com/writing/llm-evaluators/)** - Comprehensive analysis of LLM-as-Judge effectiveness

5. **[Agora - 10 Lessons Building Voice AI](https://www.agora.io/en/blog/lessons-learned-building-voice-ai-agents/)** - 12 months of production voice AI lessons

### Voice AI Specific

6. **[VAPI Evals Blog](https://vapi.ai/blog/evals)** - Native eval support for VAPI agents

7. **[Hamming AI](https://hamming.ai/)** - Voice agent testing platform (YC-backed)

8. **[a16z Voice AI Agents 2025](https://a16z.com/ai-voice-agents-2025-update/)** - Industry landscape and trends

### Evaluation & Optimization

9. **[Evidently AI - Automated Prompt Optimization](https://www.evidentlyai.com/blog/automated-prompt-optimization)** - Open-source prompt optimization

10. **[AutoGen AgentOptimizer](https://microsoft.github.io/autogen/0.2/docs/notebooks/agentchat_agentoptimizer/)** - Microsoft's agent optimization framework

---

## Appendix: Quick Start

### Minimum Viable Implementation

If you want to start tomorrow with minimal infrastructure:

1. **Export Cekura failures** → CSV or Supabase table
2. **Run weekly analysis prompt:**
   ```
   Here are 20 failed calls from this week.
   Identify the top 3 failure patterns, their root causes,
   and specific prompt changes that would fix them.
   ```
3. **Manually apply fixes** with before/after Cekura score tracking
4. **Build automation** around what works

This gets you 80% of the value with 20% of the infrastructure.

---

*Document created: January 31, 2026*
*Based on research from OpenAI, Stanford DSPy, Databricks, Moody's, Agora, and voice AI production case studies*
