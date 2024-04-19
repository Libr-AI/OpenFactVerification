# Loki Development Guide

This documentation page provides a guide for developers to want to contribute to the Loki project, for versions v0.0.2 and later.

## Loki Framework Introduction

Loki leverage state-of-the-art language models to verify the veracity of textual claims. The pipeline is designed to be modular in `factcheck/core/`, which include the following components:

- **Decomposer:** Breaks down extensive texts into digestible, independent claims, setting the stage for detailed analysis.
- **Checkworthy:** Assesses each claim's potential significance, filtering out vague or ambiguous statements to focus on those that truly matter. For example, vague claims like "MBZUAI has a vast campus" are considered unworthy because of the ambiguous nature of "vast."
- **Query Generator:** Transforms check-worthy claims into precise queries, ready to navigate the vast expanse of the internet in search of truth.
- **Evidence Retriever:** Ventures into the digital realm, retrieving relevant evidence that forms the foundation of informed verification.
- **ClaimVerify:** Examines the gathered evidence, determining the veracity of each claim to uphold the integrity of information.

For each component,

## New LLM Support


## New Search Engine Support


## New Language Support


## Prompt Optimization


## Others
