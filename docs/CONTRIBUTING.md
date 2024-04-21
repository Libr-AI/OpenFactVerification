# Contribute to Loki

Welcome and thank you for your interest in the Loki project! We welcome contributions and feedback from the community. This document outlines the process for contributing to the project.

## How to Contribute

We recommend a few best practices to make your contributions or reported errors easier to assist with.

### For Pull Requests

* PRs should be titled descriptively, and be opened with a brief description of the scope and intent of the new contribution.
* New features should have appropriate documentation added alongside them.
* Aim for code maintainability, and minimize code copying.

### For Feature Requests

* Provide a short paragraph's worth of description. What is the feature you are requesting? What is its motivation, and an example use case of it? How does this differ from what is currently supported?

### For Bug Reports

* Provide a short description of the bug.
* Provide a reproducible example--what is the command you run with our library that results in this error? Have you tried any other steps to resolve it?
* Provide a full error traceback of the error that occurs, if applicable. A one-line error message or small screenshot snippet is unhelpful without the surrounding context.
* Note what version of the codebase you are using, and any specifics of your environment and setup that may be relevant.

## Code Style

Loki uses [black](https://github.com/psf/black) and [flake8](https://pypi.org/project/flake8/) to enforce code style, via [pre-commit](https://pre-commit.com/). Before submitting a pull request, please run the following commands to ensure your code is properly formatted:

```bash
pip install pre-commit
pre-commit install
```

## How Can I Get Involved?

There are a number of distinct ways to contribute to Loki:

* Implement new features or fix bugs by submitting a pull request: If you want to use a new model or retriever, or if you have an idea for a new feature, we would love to see your contributions.
* We have our [development plan](https://github.com/Libr-AI/OpenFactVerification/tree/main/docs/development_plan.md) that outlines the roadmap for the project. If you are interested in contributing to any of the tasks, please join our [Discord](https://discord.gg/NRge6RS7) and direct message to @Haonan Li.

We hope you find this project interesting and would like to contribute to it. If you have any questions, please feel free to reach out to us on our [Discord](https://discord.gg/NRge6RS7).
