# Loki Development Guide

This documentation page provides a guide for developers to want to contribute to the Loki project, for versions v0.0.2 and later.

## Loki Framework Introduction

Loki leverage state-of-the-art language models to verify the veracity of textual claims. The pipeline is designed to be modular in `factcheck/core/`, which include the following components:

- **Decomposer:** Breaks down extensive texts into digestible, independent claims, setting the stage for detailed analysis.
- **Checkworthy:** Assesses each claim's potential significance, filtering out vague or ambiguous statements to focus on those that truly matter. For example, vague claims like "MBZUAI has a vast campus" are considered unworthy because of the ambiguous nature of "vast."
- **Query Generator:** Transforms check-worthy claims into precise queries, ready to navigate the vast expanse of the internet in search of truth.
- **Evidence Retriever:** Ventures into the digital realm, retrieving relevant evidence that forms the foundation of informed verification.
- **ClaimVerify:** Examines the gathered evidence, determining the veracity of each claim to uphold the integrity of information.

To support each component's functionality, Loki relies on the following utils:
- **Language Model:** Currently, 4 out of 5 components (including: Decomposer, Checkworthy, Query Generator, and  ClaimVerify) use the language model (LLMs) to perform their tasks. The supported LLMs are defined in `factcheck/core/utils/llmclient/` and can be easily extended to support more LLMs.
- **Prompt:** The prompt is a crucial part of the LLMs, and is usually optimized for each LLM to achieve the best performance. The prompt is defined in `factcheck/core/utils/prompt/` and can be easily extended to support more prompts.


## New LLM Support

A new LLM should be defined in `factcheck/core/utils/llmclient/` and should be a subclass of `BaseClient` from `factcheck/core/utils/llmclient/base.py`. The LLM should implement the `_call` method, which take a single string input and return a string output.

> **_Note_:**
> To ensure the sanity of the pipeline, the output of the LLM should be a compiled-code-based string, which can be directly parsed by python `eval` method. Usually, the output should be a `list` or `dict` in the form of a string.

We find that ChatGPT [json_mode](https://platform.openai.com/docs/guides/text-generation/json-mode) is a good choice for the LLM, as it can generate structured output.
To support a new LLM, you may need to implement a post-processing to convert the output of the LLM to a structured format.

## New Search Engine (Retriever) Support

Evidence retriever should be defined in `factcheck/core/Retriever/` and should be a subclass of `EvidenceRetriever` from `factcheck/core/Retriever/base.py`. The retriever should implement the `retrieve_evidence` method.

## New Language Support

To support a new language, you need to create a new file in `factcheck/utils/prompt/` with the name `<llm>_prompt_<language_iso>.py`. For example, to create a prompt suite for ChatGPT in Chinese, you can create a file named `chatgpt_prompt_zh.py`.

The prompt file should contains a class which is a subclass of `BasePrompt` from `factcheck/core/utils/prompt/base.py`, and been registered in `factcheck/utils/prompt/__init__.py`.


## Prompt Optimization

To optimize the prompt for a specific LLM, you can modify the prompt in `factcheck/utils/prompt/`. We will release a minimal test suite to evaluate the performance of the prompt in the future.

## Others
