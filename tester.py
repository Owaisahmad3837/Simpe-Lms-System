from flask import Flask, render_template, request, session, redirect
app = Flask(__name__)

@app.route('/')
def about():
    return render_template('admin_dashborad.html')
if __name__ == "__main__":
    app.run(debug=True)