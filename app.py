from flask import Flask, render_template, request, send_file
import qrcode
import os
import json
from datetime import datetime
import uuid
import pytz

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/qrcodes'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DATA_FILE = 'message_data.json'
SG_TIMEZONE = pytz.timezone('Asia/Singapore')

# Load or create message data file
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        messages = json.load(f)
else:
    messages = {}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = request.form.get('message')
        time_str = request.form.get('unlock_time')  # Format: YYYY-MM-DDTHH:MM

        if text and time_str:
            qr_id = str(uuid.uuid4())
            unlock_time = datetime.strptime(time_str, "%Y-%m-%dT%H:%M")
            unlock_time = SG_TIMEZONE.localize(unlock_time)

            messages[qr_id] = {
                "text": text,
                "unlock_time": unlock_time.strftime("%Y-%m-%d %H:%M:%S")
            }

            with open(DATA_FILE, 'w') as f:
                json.dump(messages, f)

            qr_url = request.host_url + 'unlock/' + qr_id
            qr_img = qrcode.make(qr_url)
            qr_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{qr_id}.png")
            qr_img.save(qr_path)

            return render_template("result.html", image_file=f"{qr_id}.png", qr_id=qr_id)

    return render_template('index.html')

@app.route('/unlock/<qr_id>')
def unlock(qr_id):
    now = datetime.now(SG_TIMEZONE)

    if qr_id not in messages:
        return "Invalid QR code.", 404

    unlock_str = messages[qr_id]["unlock_time"]
    unlock_time = datetime.strptime(unlock_str, "%Y-%m-%d %H:%M:%S")
    if unlock_time.tzinfo is None:
        unlock_time = SG_TIMEZONE.localize(unlock_time)

    if now >= unlock_time:
        return render_template('unlocked.html', message=messages[qr_id]["text"])
    else:
        return render_template('locked.html', unlock_time=unlock_time.strftime("%b %d, %Y %I:%M %p"))


@app.route('/download/<filename>')
def download(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
