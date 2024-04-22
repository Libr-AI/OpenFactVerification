from flask import Flask, request, render_template
import argparse

from factcheck.utils.utils import load_yaml
from factcheck import FactCheck

app = Flask(__name__, static_folder="assets")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        response = request.form["response"]
        if response == "":
            return render_template("input.html")
        response_list = factcheck_instance.check_response(response)
        return render_template("result.html", responses=response_list)

    return render_template("input.html")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="gpt-4-0125-preview")
    parser.add_argument("--prompt", type=str, default="chatgpt_prompt")
    parser.add_argument("--retriever", type=str, default="serper")
    parser.add_argument("--api_config", type=str, default="factcheck/config/api_config.yaml")
    args = parser.parse_args()

    # Load API config from yaml file
    try:
        api_config = load_yaml(args.api_config)
    except Exception as e:
        print(f"Error loading api config: {e}")
        api_config = {}

    factcheck_instance = FactCheck(
        default_model=args.model,
        api_config=api_config,
        prompt=args.prompt,
        retriever=args.retriever,
    )

    app.run(host="0.0.0.0", port=2024, debug=True)
