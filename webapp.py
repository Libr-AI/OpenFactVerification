from flask import Flask, request, render_template
from factcheck.core.FactCheck import FactCheck

app = Flask(__name__)

factcheck_instance = FactCheck()


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
    app.run(host="0.0.0.0", port=2024, debug=True)
