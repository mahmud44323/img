from flask import Flask, request, jsonify, send_from_directory
import os
import cv2
import numpy as np
from skimage import restoration

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def enhance_image(image_path, method='sharpen'):
    image = cv2.imread(image_path)
    if method == 'sharpen':
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        enhanced_image = cv2.filter2D(image, -1, kernel)
    elif method == 'denoise':
        enhanced_image = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
    elif method == 'deblur':
        enhanced_image = restoration.unsupervised_wiener(image, np.array([[1, 1], [1, 1]]))[0]
        enhanced_image = (255 * enhanced_image).astype(np.uint8)
    else:
        enhanced_image = image
    enhanced_path = os.path.join(app.config['UPLOAD_FOLDER'], 'enhanced_image.png')
    cv2.imwrite(enhanced_path, enhanced_image)
    return enhanced_path

@app.route('/')
def index():
    return '''
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
            <form id="upload-form" enctype="multipart/form-data">
                <div class="form-group">
                    <input type="file" class="form-control" name="file" required accept="image/*">
                </div>
                <div class="form-group">
                    <label for="method">Enhancement Method:</label>
                    <select class="form-control" name="method">
                        <option value="sharpen">Sharpen</option>
                        <option value="denoise">Denoise</option>
                        <option value="deblur">Deblur</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-primary">Enhance Image</button>
            </form>
            <div id="preview" class="mt-4 text-center"></div>
        </div>
        <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
        <script>
            $(document).ready(function() {
                $('#upload-form').on('submit', function(e) {
                    e.preventDefault();
                    var formData = new FormData(this);
                    $.ajax({
                        type: 'POST',
                        url: '/upload',
                        data: formData,
                        contentType: false,
                        processData: false,
                        success: function(response) {
                            $('#preview').html('<h3>Enhanced Image Preview:</h3><img src="' + response.image_url + '" alt="Enhanced Image" class="img-fluid">');
                        },
                        error: function() {
                            $('#preview').html('<p class="text-danger">An error occurred. Please try again.</p>');
                        }
                    });
                });
            });
        </script>
    </body>
    </html>
    '''

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    method = request.form.get('method', 'sharpen')
    enhanced_image_path = enhance_image(file_path, method)
    enhanced_image_url = f'/uploads/enhanced_image.png'
    
    return jsonify({'image_url': enhanced_image_url})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)
