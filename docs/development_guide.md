# Development Guide

This documentation page provides a guide for developers to want to contribute to the Loki project, for versions v0.0.3 and later.

- [Development Guide](#development-guide)
  - [Framework Introduction](#framework-introduction)
  - [Development Plan](#development-plan)


## Framework Introduction

Loki leverage state-of-the-art language models to verify the veracity of textual claims. The pipeline is designed to be modular in `factcheck/core/`, which include the following components:

- **Decomposer:** Breaks down extensive texts into digestible, independent claims, setting the stage for detailed analysis. As well as provide the mapping between the original text and the decomposed claims.
- **Checkworthy:** Assesses each claim's potential checkworthiness, filtering out vague or ambiguous statements, as well as the statement of opinion. For example, vague claims like "MBZUAI has a vast campus" are considered unworthy because of the ambiguous nature of "vast."
- **Query Generator:** Transforms check-worthy claims into precise queries, ready to navigate the vast expanse of the internet in search of evidences.
- **Evidence Retriever:** Retrieve relevant evidence that forms the foundation of informed verification, currently, for open-domain questions, we now use the google search (Serper API).
- **ClaimVerify:** Judges each evidence against the claim, determining it is supporting, refuting, or irrelevant.

To support each component's functionality, Loki relies on the following utils:
- **Language Model:** Currently, 4 out of 5 components (including: Decomposer, Checkworthy, Query Generator, and  ClaimVerify) use the language model (LLMs) to perform their tasks. The supported LLMs are defined in `factcheck/core/utils/llmclient/` and can be easily extended to support more LLMs.
- **Prompt:** The prompt is a crucial part of the LLMs, and is usually optimized for each LLM to achieve the best performance. The prompt is defined in `factcheck/core/utils/prompt/` and can be easily extended to support more prompts.

### Support a New LLM Client

A new LLM should be defined in `factcheck/core/utils/llmclient/` and should be a subclass of `BaseClient` from `factcheck/core/utils/llmclient/base.py`. The LLM should implement the `_call` method, which take a single string input and return a string output.

> **_Note_:**
> To ensure the sanity of the pipeline, the output of the LLM should be a compiled-code-based string, which can be directly parsed by python `eval` method. Usually, the output should be a `list` or `dict` in the form of a string.

We find that ChatGPT [json_mode](https://platform.openai.com/docs/guides/text-generation/json-mode) is a good choice for the LLM, as it can generate structured output.
To support a new LLM, you may need to implement a post-processing to convert the output of the LLM to a structured format.

### Support a New Search Engine (Retriever)

Evidence retriever should be defined in `factcheck/core/Retriever/` and should be a subclass of `EvidenceRetriever` from `factcheck/core/Retriever/base.py`. The retriever should implement the `retrieve_evidence` method.

### Support a New Language

To support a new language, you need to create a new file in `factcheck/utils/prompt/` with the name `<llm>_prompt_<language_iso>.py`. For example, to create a prompt suite for ChatGPT in Chinese, you can create a file named `chatgpt_prompt_zh.py`.

The prompt file should contains a class which is a subclass of `BasePrompt` from `factcheck/core/utils/prompt/base.py`, and been registered in `factcheck/utils/prompt/__init__.py`.


### Prompt Optimization

To optimize the prompt for a specific LLM, you can modify the prompt in `factcheck/utils/prompt/`. After optimization, you can run our minimal test in `script/minimal_test.py`, you are also welcomed to add more test cases to the minimal test set in `script/minimal_test.json`.



## Development Plan

As Loki continues to evolve, our development plan focuses on broadening capabilities and enhancing flexibility to meet the diverse needs of our users. Here are the key areas we are working on:

### 1. Support for Multiple Models
- **Broader Model Compatibility:**
  - Integration with leading AI models besides ChatGPT and Claude to diversify fact-checking capabilities, including Command R and Gemini.
  - Implementation of self-hosted model options for enhanced privacy and control, e.g., FastChat, TGI, and vLLM.

### 2. Model-specific Prompt Engineering
- **Unit Testing for Prompts:**
  - Develop robust unit tests for each step to ensure prompt reliability and accuracy across different scenarios.

### 3. Expanded Search Engine Support
- **Diverse Search Engines:**
  - Incorporate a variety of search engines including Bing, scraperapi to broaden search capabilities.
  - Integration with [Searxng](https://github.com/searxng/searxng), an open-source metasearch engine.
  - Support for specialized indexes like LlamaIndex and Langchain, and the ability to search local documents.

### 4. Deployment and Scalability
- **Dockerization:**
  - Packaging Loki into Docker containers to simplify deployment and scale-up operations, ensuring Loki can be easily set up and maintained across different environments.

### 5. Multi-lingual Support
- **Language Expansion:**
  - Support for additional languages beyond English, including Chinese, Arabic, etc, to cater to a global user base.


We are committed to these enhancements to make Loki not just more powerful, but also more adaptable to the needs of a global user base. Stay tuned as we roll out these exciting developments!
