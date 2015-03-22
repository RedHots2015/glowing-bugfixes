from os import path
from hashlib import sha1

from flask import Flask, request, url_for, render_template, redirect, send_from_directory
from flask_wtf import Form
from flask_wtf.file import FileField, FileAllowed, FileRequired
from flask.ext.sqlalchemy import SQLAlchemy

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
    continuity = db.Column(db.Float)
    age = db.Column(db.Integer)

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
        db.session.commit()

        return redirect(url_for('refine', id=mole.id))

    return render_template('index.html', form=form)

@app.route('/refine/<string:id>')
def refine(id):
    mole = Mole.query.filter(Mole.id == id).first_or_404()
    return render_template('refine.html', url=url_for('uploads', filename=mole.filename))

@app.route('/uploads/<string:filename>')
def uploads(filename):
    print(filename)
    return send_from_directory('uploads', filename)

if __name__ == '__main__':
    app.debug = True
    db.drop_all()
    db.create_all()
    app.run(host="0.0.0.0")
