import os
from flask import Flask, request, render_template_string
from openai import OpenAI
from werkzeug.utils import secure_filename
import base64

# Fetch API key from environment variable
api_key = os.getenv("API_KEY")
if not api_key:
    raise EnvironmentError("API_KEY environment variable is not set")

client = OpenAI(api_key=api_key)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

HTML_TEMPLATE = '''
<!doctype html>
<html>
<head>
  <title>ConSim 1.0</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f4; }
    h2 { color: #333; }
    textarea { width: 100%; }
    .response-box {
      width: 100%;
      height: 300px;
      white-space: pre-wrap;
      overflow-y: scroll;
      padding: 10px;
      background-color: #fff;
      border: 1px solid #ccc;
    }
  </style>
</head>
<body>
<h2>ConSim 1.0 - Simulated Market Research</h2>
<form method=post enctype=multipart/form-data>
  <label for="prompt">Enter your marketing prompt:</label><br>
  <textarea name=prompt rows=10></textarea><br><br>

  <label for="image">Upload image (optional):</label><br>
  <input type=file name=image><br><br>

  <label for="use_image">Include image in simulation:</label>
  <input type=checkbox name=use_image checked><br><br>

  <input type=submit value="Run Simulation">
</form>

{% if response %}
<h3>Simulated Feedback:</h3>
<div class="response-box">{{ response }}</div>
{% endif %}
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    response = None
    if request.method == 'POST':
        prompt = request.form['prompt']
        image = request.files.get('image')
        use_image = 'use_image' in request.form

        image_path = None
        if image and image.filename and use_image:
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

        response = call_llm(prompt, image_path)
    return render_template_string(HTML_TEMPLATE, response=response)

def call_llm(prompt, image_path):
    try:
        if image_path:
            with open(image_path, "rb") as img_file:
                image_base64 = base64.b64encode(img_file.read()).decode('utf-8')

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]

            completion = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=messages,
                max_tokens=1000
            )
        else:
            messages = [
                {"role": "system", "content": "You are simulating a consumer responding to a marketing campaign."},
                {"role": "user", "content": prompt}
            ]
            completion = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=1000
            )

        return completion.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

if __name__ == '__main__':
    app.run(debug=True)
