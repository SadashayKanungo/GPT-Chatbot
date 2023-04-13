from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', script_result="")

@app.post('/newbot')
def generate_new_bot():
    url = request.form.get('url')
    return render_template('index.html', script_result = f"<script>{url}</script>")

if __name__ == "__main__":
    app.run(debug=True)