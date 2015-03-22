from os import path
import os
from hashlib import sha1

from flask import Flask, request, url_for, render_template, redirect, send_from_directory, jsonify
from flask_wtf import Form
from flask_wtf.file import FileField, FileAllowed, FileRequired
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError


app = Flask('Glow Bugfixes', static_folder='static/dist', static_url_path='/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SECRET_KEY'] = 'Super Secret'
db = SQLAlchemy(app)

class UploadForm(Form):
    """
    Having a upload form
    """
    photo = FileField(u'Photo', validators=[
        FileRequired(), 
        FileAllowed(['jpg'], 'images only')
    ])


class Mole(db.Model):
    id = db.Column(db.String(120), primary_key=True)
    filename = db.Column(db.String(80), unique=True)
    diameter = db.Column(db.Float)
    symmetry = db.Column(db.Float)
    h = db.Column(db.Float)
    s = db.Column(db.Float)
    v = db.Column(db.Float)
    age = db.Column(db.Integer)
    mask_cx = db.Column(db.Float)
    mask_cy = db.Column(db.Float)
    mask_r = db.Column(db.Float)
    status = db.Column(db.Integer)

def request_wants_json():
        best = request.accept_mimetypes \
                .best_match(['application/json', 'text/html'])
        return best == 'application/json' and \
            request.accept_mimetypes[best] > \
            request.accept_mimetypes['text/html']


def chunks(data):
    def fun():
        return data.read(1024)
    return fun

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Renders the home page
    """
    
    form = UploadForm()
    if form.validate_on_submit():
        hash = sha1()
        
        for chunk in iter(lambda: form.photo.data.read(1024), b''):
            hash.update(chunk)

        form.photo.data.seek(0)

        hash = hash.hexdigest()
        filename = hash + '.jpg' 
        form.photo.data.save(path.join('uploads', filename))        
        
        mole = Mole()
        mole.id = hash
        mole.filename = filename

        db.session.add(mole)
        try:
            db.session.commit()
        except IntegrityError:
            form.errors['photo'] = ['Image already exists']
            
            if request_wants_json():
                return jsonify({'errors': form.errors})

            return render_template('index.html', form=form)


        if request_wants_json():
            return jsonify({
                'id': mole.id,
                'url': url_for('uploads', filename=filename)
            })

        return redirect(url_for('refine', id=mole.id))


        if request_wants_json():
            return jsonify({'errors': form.errors})

    return render_template('index.html', form=form)

@app.route('/refine/<string:id>')
def refine(id):
    mole = Mole.query.filter(Mole.id == id).first_or_404()
    mole.mask_cx = request.json['cx']
    mole.mask_cy = request.json['cy']
    mole.mask_r = request.json['radius']
   
    
    db.session.merge(mole)
    db.session.commit()

    os.spawnlp(os.P_WAIT, 'algorithm.py', 'algorithm.py', id)

    return jsonify({'OK': 'True'}) 

@app.route('/updates/<string:id>')
def update(id):
    mole = Mole.query.filter(Mole.id == id).first_or_404()
    return jsonify({'status': mole.status})

@app.route('/uploads/<string:filename>')
def uploads(filename):
    print(filename)
    return send_from_directory('uploads', filename)


if __name__ == '__main__':
    app.debug = True
    db.drop_all()
    db.create_all()
    app.run(host="0.0.0.0")
