from flask import Flask, send_file, render_template_string

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Latency Graph</title>
</head>
<body style="font-family: Arial, sans-serif; background: #f4f4f9; color: #333; text-align: center; padding: 50px;">

    <h1 style="color: #4a90e2; margin-bottom: 40px;">📶 Latency Graph</h1>

    <img src="/image" alt="Latency Graph" width="800" style="border: 2px solid #ddd; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/><br><br>

    <a href="/download" download>
        <button 
            onmouseover="this.style.backgroundColor='#357ABD'; this.style.transform='scale(1.05)';"
            onmouseout="this.style.backgroundColor='#4a90e2'; this.style.transform='scale(1)';"
            style="background-color: #4a90e2; color: white; border: none; padding: 12px 25px; border-radius: 8px; font-size: 16px; cursor: pointer; box-shadow: 0 2px 5px rgba(0,0,0,0.2); transition: all 0.3s ease;">
            ⬇️ Download Graph
        </button>
    </a>

    <!-- Footer Start -->
<div style="background-color: #1f1f1f; color: #ccc; padding: 30px 10px; margin-top: 50px; font-size: 14px; text-align: center;">

    <p style="margin: 10px 0;">
        Made with 💙 by 
        <a href="https://github.com/Parth-Khosla/Azure-benchmark-VM" style="color: #4a90e2; text-decoration: none;" target="_blank">Parth Khosla</a>
    </p>

    <p style="margin: 10px 0;">
        Project Repository: 
        <a href="https://github.com/Parth-Khosla/Azure-benchmark-VM" style="color: #4a90e2; text-decoration: none;" target="_blank">Azure-benchmark-VM</a>
    </p>

    <p style="color: #777; margin-top: 20px;">&copy; 2025 Parth Khosla. All rights reserved.</p>

</div>
<!-- Footer End -->

</body>
</html>

"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/image')
def image():
    return send_file('latency_graph.png', mimetype='image/png')

@app.route('/download')
def download():
    return send_file('latency_graph.png', as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
