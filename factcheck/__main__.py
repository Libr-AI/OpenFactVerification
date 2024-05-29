import json
import argparse

from factcheck.utils.llmclient import CLIENTS
from factcheck.utils.multimodal import modal_normalization
from factcheck.utils.utils import load_yaml
from factcheck import FactCheck


def check(args):
    """factcheck

    Args:
        model (str): gpt model used for factchecking
        modal (str): input type, supported types are str, text file, speech, image, and video
        input (str): input content or path to the file
    """
    # Load API config from yaml file
    try:
        api_config = load_yaml(args.api_config)
    except Exception as e:
        print(f"Error loading api config: {e}")
        api_config = {}

    factcheck = FactCheck(
        default_model=args.model, client=args.client, api_config=api_config, prompt=args.prompt, retriever=args.retriever
    )

    content = modal_normalization(args.modal, args.input)
    res = factcheck.check_text(content)
    print(json.dumps(res, indent=4))

    # Save the results to lark (only for local testing)
    try:
        from factcheck.utils import lark

        lark.save_json_to_lark_by_level(res)
    except:  # noqa
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="gpt-4o")
    parser.add_argument("--client", type=str, default=None, choices=CLIENTS.keys())
    parser.add_argument("--prompt", type=str, default="chatgpt_prompt")
    parser.add_argument("--retriever", type=str, default="serper")
    parser.add_argument("--modal", type=str, default="text")
    parser.add_argument("--input", type=str, default="demo_data/text.txt")
    parser.add_argument("--api_config", type=str, default="factcheck/config/api_config.yaml")
    args = parser.parse_args()

    check(args)
