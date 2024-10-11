from flask import Flask, request, redirect, send_from_directory, render_template_string
import os
import cv2
import numpy as np
from skimage import restoration

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Function to enhance image quality
def enhance_image(image_path, method='sharpen'):
    img = cv2.imread(image_path)

    if method == 'sharpen':
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        enhanced = cv2.filter2D(img, -1, kernel)

    elif method == 'denoise':
        enhanced = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)

    elif method == 'deblur':
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        deconvolved = restoration.wiener(gray, np.ones((5, 5)), 1, clip=True)
        enhanced = np.clip(deconvolved * 255, 0, 255).astype(np.uint8)

    else:
        return img

    enhanced_path = os.path.join(app.config['UPLOAD_FOLDER'], 'enhanced_image.png')
    cv2.imwrite(enhanced_path, enhanced)

    return enhanced_path

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Image Enhancer</title>
        <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
        <style>
            body {
                background-color: #f5f5f5;
                font-family: 'Roboto', sans-serif;
            }
            .container {
                max-width: 600px;
                margin-top: 50px;
                background-color: #fff;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }
            h1 {
                text-align: center;
                color: #333;
                margin-bottom: 20px;
            }
            .btn {
                width: 100%;
                margin-top: 10px;
            }
            .form-group {
                margin-bottom: 15px;
            }
            footer {
                text-align: center;
                margin-top: 20px;
            }
            #preview {
                display: none;
                width: 100%;
                height: auto;
                margin-bottom: 20px;
                border-radius: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Upload an Image to Enhance</h1>
            <input type="file" class="form-control" id="file-input" required accept="image/*">
            <img id="preview" src="" alt="Image Preview">
            <form id="upload-form" action="/upload" method="post" enctype="multipart/form-data">
                <input type="hidden" name="file" id="file-data">
                <div class="form-group">
                    <select class="form-control" name="method">
                        <option value="sharpen">Sharpen</option>
                        <option value="denoise">Denoise</option>
                        <option value="deblur">Deblur</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-primary">Enhance Image</button>
            </form>
            <footer>
                <p>&copy; 2024 Image Enhancer</p>
            </footer>
        </div>
        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.2/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
        <script>
            document.getElementById('file-input').addEventListener('change', function() {
                const file = this.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(event) {
                        const preview = document.getElementById('preview');
                        preview.src = event.target.result;
                        preview.style.display = 'block';
                        document.getElementById('file-data').value = event.target.result;
                    };
                    reader.readAsDataURL(file);
                }
            });

            document.getElementById('upload-form').addEventListener('submit', function(event) {
                const fileInput = document.getElementById('file-input');
                const file = fileInput.files[0];
                if (!file) {
                    event.preventDefault();
                    alert('Please upload an image.');
                }
            });
        </script>
    </body>
    </html>
    ''')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    method = request.form.get('method', 'sharpen')

    try:
        enhanced_image_path = enhance_image(file_path, method)
    except Exception as e:
        return f"<h2>Error during image processing: {str(e)}</h2>"

    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Enhanced Image</title>
        <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{
                background-color: #f5f5f5;
                font-family: 'Roboto', sans-serif;
            }}
            .container {{
                max-width: 600px;
                margin-top: 50px;
                background-color: #fff;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }}
            h1 {{
                text-align: center;
                color: #333;
            }}
            img {{
                width: 100%;
                height: auto;
                border-radius: 10px;
            }}
            footer {{
                text-align: center;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Enhanced Image</h1>
            <img src="/uploads/enhanced_image.png" alt="Enhanced Image">
            <br>
            <a href="/" class="btn btn-primary" style="margin-top: 10px;">Upload Another Image</a>
        </div>
        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.2/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    </body>
    </html>
    '''

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)  # Running on port 5003
