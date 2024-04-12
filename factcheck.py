from factcheck import FactCheck
from factcheck.utils.multimodal import modal_normalization
import argparse
import json


def main(model: str, modal: str, input: str):
    """factcheck

    Args:
        model (str): gpt model used for factchecking
        modal (str): input type, supported types are str, text file, speech, image, and video
        input (str): input content or path to the file
    """
    factcheck = FactCheck(default_model=model)
    content = modal_normalization(modal, input)
    res = factcheck.check_response(content)
    print(json.dumps(res["step_info"], indent=4))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="gpt-4-0125-preview")
    parser.add_argument("--modal", type=str, default="text")
    parser.add_argument("--input", type=str, default="demo_data/text.txt")
    args = parser.parse_args()

    main(args.model, args.modal, args.input)
