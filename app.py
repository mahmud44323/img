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
    # Load the image
    image = cv2.imread(image_path)

    # Enhance based on the selected method
    if method == 'sharpen':
        kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
        enhanced_image = cv2.filter2D(image, -1, kernel)
    elif method == 'denoise':
        enhanced_image = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
    elif method == 'deblur':
        enhanced_image = restoration.unsupervised_wiener(image, np.array([[1, 1], [1, 1]]))[0]
        enhanced_image = (255 * enhanced_image).astype(np.uint8)
    else:
        enhanced_image = image

    # Save the enhanced image
    enhanced_path = os.path.join(app.config['UPLOAD_FOLDER'], 'enhanced_image.png')
    cv2.imwrite(enhanced_path, enhanced_image)

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
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons">
    </head>
    <body>
        <div class="container mt-5">
            <h1 class="text-center">Upload an Image to Enhance</h1>
            <input type="file" class="form-control" id="file-input" required accept="image/*">
            <img id="preview" src="" alt="Image Preview" style="max-width: 100%; height: auto; display: none;">
            <form id="upload-form" action="/upload" method="post" enctype="multipart/form-data">
                <input type="hidden" name="file" id="file-data">
                <div class="form-group">
                    <label for="method">Enhancement Method:</label>
                    <select class="form-control" name="method" id="method">
                        <option value="sharpen">Sharpen</option>
                        <option value="denoise">Denoise</option>
                        <option value="deblur">Deblur</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-primary">Enhance Image</button>
            </form>
            <footer class="mt-4">
                <p class="text-center">&copy; 2024 Image Enhancer</p>
            </footer>
        </div>
        <script>
            document.getElementById('file-input').addEventListener('change', function() {
                const file = this.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        document.getElementById('preview').src = e.target.result;
                        document.getElementById('preview').style.display = 'block';
                    }
                    reader.readAsDataURL(file);
                    const formData = new FormData();
                    formData.append("file", file);
                    document.getElementById('file-data').value = file.name;
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
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons">
    </head>
    <body>
        <div class="container mt-5 text-center">
            <h1>Enhanced Image</h1>
            <img src="/uploads/enhanced_image.png" alt="Enhanced Image" style="max-width: 100%; height: auto;">
            <a href="/" class="btn btn-primary mt-3">Upload Another Image</a>
        </div>
    </body>
    </html>
    '''

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)
