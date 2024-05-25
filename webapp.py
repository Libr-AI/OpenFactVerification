from flask import Flask, request, render_template, jsonify
import argparse
import json

from factcheck.utils.utils import load_yaml
from factcheck import FactCheck

app = Flask(__name__, static_folder="assets")


# Define the custom filter
def zip_lists(a, b):
    return zip(a, b)


# Register the filter with the Jinja2 environment
app.jinja_env.filters["zip"] = zip_lists


# Occurrences count filter
def count_occurrences(input_dict, target_string, key):
    input_list = [item[key] for item in input_dict]
    return input_list.count(target_string)


app.jinja_env.filters["count_occurrences"] = count_occurrences


# Occurrences count filter
def filter_evidences(input_dict, target_string, key):
    return [item for item in input_dict if target_string == item[key]]


app.jinja_env.filters["filter_evidences"] = filter_evidences


# Claim statistics
def claim_statistic(response):
    return {
        "total_claims": len(response["claim_details"]),
        "well_supported_claims": len([claim for claim in response["claim_details"] if (claim["factuality"] == 1)]),
        "controversial_claims": len([claim for claim in response["claim_details"] if (0 < claim["factuality"] < 1)]),
        "conflicted_claims": len([claim for claim in response["claim_details"] if (claim["factuality"] == 0)]),
    }


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        response = request.form["response"]
        if response == "":
            return render_template("input.html")
        response = factcheck_instance.check_response(response)

        # save the response json file
        with open("assets/response.json", "w") as f:
            json.dump(response, f)

        claim_sta = claim_statistic(response)
        return render_template("LibrAI_fc.html", responses=response, shown_claim=0, claim_statistic=claim_sta)

    return render_template("input.html")


# @app.route("/", methods=["GET", "POST"])
# def index():
#     # load the response json file
#     import json
#     with open('response.json') as f:
#         response = json.load(f)
#     claim_sta=claim_statistic(response)
#     return render_template("LibrAI_fc.html", responses=response, shown_claim=0, claim_statistic=claim_sta)


@app.route("/shownClaim/<content_id>")
def get_content(content_id):
    # load the response json file
    import json

    with open("assets/response.json") as f:
        response = json.load(f)

    claim_sta = claim_statistic(response)
    return render_template("LibrAI_fc.html", responses=response, shown_claim=(int(content_id) - 1), claim_statistic=claim_sta)


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
