from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/vehicles.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'  # Folder for uploaded images
app.secret_key = 'your_secret_key'  # Required for flashing messages
db = SQLAlchemy(app)

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Vehicle model
class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100), nullable=False)
    plate_number = db.Column(db.String(20), unique=True, nullable=False)
    image_file = db.Column(db.String(120), nullable=False)
    rent_per_day = db.Column(db.Float, nullable=False)
    passenger_capacity = db.Column(db.Integer, nullable=False)
    ratings = db.Column(db.Float, nullable=True)
    availability = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Vehicle {self.model_name}>'

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/add_vehicle', methods=['GET', 'POST'])
def add_vehicle():
    if request.method == 'POST':
        model_name = request.form['model_name']
        plate_number = request.form['plate_number']
        rent_per_day = float(request.form['rent_per_day'])  # Convert to float
        passenger_capacity = int(request.form['passenger_capacity'])  # Convert to int
        ratings = float(request.form['ratings']) if request.form['ratings'] else None
        availability = request.form['availability'] == 'true'

        # Handle image upload
        image = request.files['image']
        if image and allowed_file(image.filename):
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

            new_vehicle = Vehicle(
                model_name=model_name,
                plate_number=plate_number,
                image_file=image_filename,
                rent_per_day=rent_per_day,
                passenger_capacity=passenger_capacity,
                ratings=ratings,
                availability=availability
            )
            db.session.add(new_vehicle)
            db.session.commit()
            flash('Vehicle added successfully!', 'success')
            return redirect(url_for('get_vehicles'))
        else:
            flash('Invalid image file. Please upload a valid image.', 'danger')

    return render_template('add_vehicle.html')

@app.route('/vehicles', methods=['GET'])
def get_vehicles():
    vehicles = Vehicle.query.all()
    return render_template('view_vehicles.html', vehicles=vehicles)

@app.route('/update_vehicle/<int:id>', methods=['GET', 'POST'])
def update_vehicle(id):
    vehicle = Vehicle.query.get_or_404(id)

    if request.method == 'POST':
        vehicle.model_name = request.form['model_name']
        vehicle.plate_number = request.form['plate_number']
        vehicle.rent_per_day = float(request.form['rent_per_day'])
        vehicle.passenger_capacity = int(request.form['passenger_capacity'])
        vehicle.ratings = float(request.form['ratings']) if request.form['ratings'] else None
        vehicle.availability = request.form['availability'] == 'true'

        # Handle image upload
        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                image_filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
                vehicle.image_file = image_filename

        db.session.commit()
        flash('Vehicle updated successfully!', 'success')
        return redirect(url_for('get_vehicles'))

    return render_template('update_vehicle.html', vehicle=vehicle)

@app.route('/delete_vehicle/<int:id>', methods=['POST'])
def delete_vehicle(id):
    vehicle = Vehicle.query.get_or_404(id)  # Fetch vehicle or return 404
    db.session.delete(vehicle)  # Remove vehicle from session
    db.session.commit()  # Commit the transaction
    flash('Vehicle deleted successfully!', 'success')  # Flash success message
    return redirect(url_for('get_vehicles'))  # Redirect back to vehicles list

def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')  # Render a home page template

if __name__ == '__main__':
    with app.app_context():  # Create an application context
        db.create_all()  # Create database and tables
    app.run(debug=True)
