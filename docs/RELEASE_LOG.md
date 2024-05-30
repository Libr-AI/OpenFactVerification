# Release Log

## v0.0.3

### New Features
1. **Keep Original Text:** Add the mapping from each claim to the position in the original text. Add `restore_claims` function to **decomposer**, to restore the decomposed claims to the original user input.
2. **Data Structure:** Define the data structure for several intermedia processing function and final output in `utils/data_class.py`.
3. **Speed Up:** Parallel the `restore_claims`, `identify_checkworthiness` and `query_generation` functions to speed up the pipeline.
4. **Token Count:** Add the token count for all component.
5. **Evidence-wise Verification:** Change the verification logic from input all evidence together within a single LLM call, to verify the claim by each evidence for each LLM call.
6. **Factuality Value:** Remove the deterministic output, change the factuality to a number in range [0,1], calculated by the judgement with each simple evidence.
7. **Webpage:** Redesign the webpage.
8. **Default LLM:** Change to GPT-4o.

### Bug fixed
1. **Serper Max Queries:** Serper API allows max of 100 queries in one request, we split the queries into multiple requests if the number of queries exceeds 100.
2. **Evidence and URL:** Link each evidence to the corresponding URL.

## v0.0.2

### New Features
1. **API Key Handling:** Transitioned from creating key files via copying to dynamically reading all API keys from a YAML file, streamlining configuration processes.
2. **Unified Configuration Dictionary:** Replaced platform-specific dictionaries with a unified dictionary that aligns with environmental variable naming conventions, enhancing consistency and maintainability.
3. **Model Switching:** Introduced a `--model` parameter that allows switching between different models, currently supporting OpenAI and Anthropic.
4. **Modular Architecture:** Restructured the codebase into one Base class file and individual class files for each model, enhancing modularity and clarity.
5. **Base Class Redefinition:** Redefined the Base class to abstract asynchronous operations and other functionalities. Users customizing models need only override three functions.
6. **Prompt Switching:** Added a `--prompt` parameter for switching between predefined prompts, initially supporting prompts for OpenAI and Anthropic.
7. **Prompt Definitions via YAML and JSON:** Enabled prompt definitions using YAML and JSON, allowing prompts to be automatically read from corresponding YAML or JSON files when the prompt parameter ends with `.yaml` or `.json`.
8. **Search Engine Switching:** Introduced a `--retriever` parameter to switch between different search engines, currently supporting Serper and Google.
9. **Webapp Frontend Optimization:** Optimized the web application frontend to prevent duplicate requests during processing, including disabling the submit button after a click and displaying a timer during processing.
10. **Client Switching:** introduce a `--client` parameter that allows switching between different client (chat API), currently support OpenAI compatible API (for local model and official model), and Anthropic chat API client.



## v0.0.1

Initial release of Loki.
