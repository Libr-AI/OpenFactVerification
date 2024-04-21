# Release Log


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
