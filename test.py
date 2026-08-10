from flask import Flask, render_template, request # type: ignore

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/contact", methods=["POST"])
def contact():

    name = request.form["name"]
    phone = request.form["phone"]
    email = request.form["email"]
    message = request.form["message"]

    print(name)
    print(phone)
    print(email)
    print(message)

    return "Form Submitted Successfully"


if __name__ == "__main__":
    app.run(debug=True)