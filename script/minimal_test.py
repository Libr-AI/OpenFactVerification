import sys
import time
import json
from tqdm import tqdm

sys.path.append("..")
from factcheck import FactCheck  # noqa: E402

# ANSI escape codes for colors
green = "\033[92m"
red = "\033[91m"
reset = "\033[0m"


def minimal_test(lang="en"):
    # Initialize the FactCheck class
    prompt = "chatgpt_prompt"
    if lang == "zh":
        prompt = "chatgpt_prompt_zh"
    factcheck = FactCheck(prompt=prompt)

    def atom_test(instance):
        response = instance["response"]
        res = factcheck.check_text(response)
        try:
            for k, v in instance["attributes"].items():
                print(f"{k}: {res[k]}, {v}")
                assert res[k] == v
            return True
        except:  # noqa E722
            return False

    with open(f"minimal_test_{lang}.json", encoding="utf-8") as f:
        test_data = json.load(f)
    num_tests = len(test_data)

    with tqdm(total=num_tests, position=0) as pbar:
        success_count = 0
        fail_count = 0
        for i, test_piece in enumerate(test_data):
            result = atom_test(test_piece)

            if result is True:
                success_count += 1
                pbar.set_postfix_str("█", refresh=False)
                pbar.colour = "green"
            else:
                fail_count += 1
                pbar.set_postfix_str("█", refresh=False)
                pbar.colour = "red"

            pbar.set_description(f"| Success: {success_count}, Failed: {fail_count}", refresh=True)
            pbar.update(1)
            time.sleep(0.1)  # Sleep for 0.1 seconds


if __name__ == "__main__":
    minimal_test()
