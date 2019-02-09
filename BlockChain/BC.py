import hashlib
import json
import os
from time import time
from flask import Flask
from flask import render_template, redirect, url_for,jsonify
from flask import request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import DateField, FloatField, IntegerField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SECRET_KEY'] = 'CTB'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donor = db.Column(db.String,nullable=False)
    donee = db.Column(db.String,nullable=False)
    money = db.Column(db.Float,nullable=False)

class Donateform(FlaskForm):
    donor = StringField("Donor", validators=[DataRequired()])
    donee = StringField("Donee", validators=[DataRequired()])
    money = FloatField("Money", validators=[DataRequired()])

db.create_all()

@app.route('/')
def index():
    return render_template('aboute.html')


@app.route('/donor', methods=['GET', 'POST'])
def donor():
    # print(request.method )
    if request.method == 'POST':
        money = request.form['money']
        donee = request.form['donee']
        info = request.form['info']
        donor = request.form['donor']
        if len(donee)< 1:
            return redirect(url_for('donor'))
        try:
            make_proof = request.form['make_proof']
        except Exception:
            make_proof = False
        write_block(money,donor,donee,info, make_proof)
        user=User(money=money,donee=donee,donor=donor)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('donor'))
    return render_template('donor.html')

@app.route('/donee', methods=['GET', 'POST'])
def donee():
    if request.method == "POST" :
        donee_selected = request.form['select']
        block_number = User.query.filter(User.donee == donee_selected).all()
        blocks_id = [r.id for r in block_number]
        block_id=int(blocks_id[0])+1
        return render_template('donee.html',block_number=block_number,block_id=block_id)
    return render_template('donee.html')

@app.route('/check', methods=[ 'POST'])
def integrity():
    results = check_blocks_integrity()
    if request.method == 'POST':
        return render_template('donee.html', results=results)
    return render_template('donee.html')

@app.route('/mining', methods=[ 'POST'])
def mining():
    if request.method == 'POST':
        max_index = int(get_next_block())

        for i in range(2, max_index):
            get_POW(i)
        return render_template('donor.html', querry=max_index)
    return render_template('donor.html')

@app.route('/aboute')
def aboute():
    return render_template('aboute.html')

@app.route('/aboutp')
def aboutp():
    return render_template('aboutp.html')

@app.route('/aboutb')
def aboutb():
    return render_template('aboutb.html')

BLOCKCHAIN_DIR = os.curdir + '/blocks/'


def check_blocks_integrity():
    result = list()
    cur_proof = - 1
    for i in range(2, int(get_next_block())):
        prev_index = str(i-1)
        cur_index = str(i)
        tmp = {'block' : '', 'result' : '', 'proof': ''}
        try:
            file_dict = json.load(open(BLOCKCHAIN_DIR + cur_index + '.json'))
            cur_hash = file_dict['prev_hash']
            cur_proof = file_dict['proof']
        except Exception as e:
            print(e)

        try:
            prev_hash = hashlib.sha256(open(BLOCKCHAIN_DIR + prev_index + '.json', 'rb').read()).hexdigest()
        except Exception as e:
            print(e)

        tmp['block'] = prev_index
        tmp['proof'] = cur_proof
        if cur_hash == prev_hash:
            tmp['result'] = 'ok'
        else:
            tmp['result'] = 'error'
        result.append(tmp)
    return result


def check_block(index):
    cur_index = str(index)
    prev_index = str(int(index) - 1)
    cur_proof = - 1
    cur_hash = 0
    prev_hash =0
    tmp = {'block' : '', 'result' : '', 'proof': ''}
    try:
        file_dict = json.load(open(BLOCKCHAIN_DIR + cur_index + '.json'))
        cur_hash = file_dict['prev_hash']
        cur_proof = file_dict['proof']
    except Exception as e:
        print(e)
    try:
        prev_hash = hashlib.sha256(open(BLOCKCHAIN_DIR + prev_index + '.json', 'rb').read()).hexdigest()
    except Exception as e:
        print(e)
    tmp['block'] = prev_index
    tmp['proof'] = cur_proof
    if cur_hash == prev_hash:
        tmp['result'] = 'ok'
    else:
        tmp['result'] = 'error'
    return tmp


def get_hash(file_name):
    file_name = str(file_name)
    if not file_name.endswith('.json'):
        file_name += '.json'
    try:
        with open(BLOCKCHAIN_DIR + file_name, 'rb') as file:
            return hashlib.sha256(file.read()).hexdigest()
    except Exception as e:
        print('File "'+file_name+'" does not exist!n', e)


def get_next_block():
    files = os.listdir(BLOCKCHAIN_DIR)
    index_list = [int(file.split('.')[0]) for file in files]
    cur_index = sorted(index_list)[-1]
    next_index = cur_index + 1
    return str(next_index)


def is_valid_proof(last_proof, proof, difficulty):
    guess = f'{last_proof}{proof}'.encode()
    guess_hash = hashlib.sha256(guess).hexdigest()
    return guess_hash[:difficulty] == '0' * difficulty


def get_POW(file_name, difficulty=1):
    # POW - proof of work
    file_name = str(file_name)
    if file_name.endswith('.json'):
        file_name = int(file_name.split('.')[0])
    else:
        file_name = int(file_name)

    last_proof = json.load(open(BLOCKCHAIN_DIR + str(file_name - 1) + '.json'))['proof']
    proof = 0
    while is_valid_proof(last_proof, proof, difficulty) is False:
        proof += 1
    cur_block = json.load(open(BLOCKCHAIN_DIR + str(file_name) + '.json'))
    cur_block['proof'] = proof
    cur_block['prev_hash'] = get_hash(str(file_name - 1))
    with open(BLOCKCHAIN_DIR + str(file_name) + '.json', 'w') as file:
        json.dump(cur_block, file, indent=4, ensure_ascii=False)


def write_block(money,donor,donee,info, make_proof=False):
    cur_index = get_next_block()
    prev_index = str(int(cur_index) - 1)
    prev_block_hash = get_hash(prev_index)
    data = {'money' : money,
            'Donor':donor,
            'Donee':donee,
            'Info':info,
            'prev_hash' : prev_block_hash,
            'timestamp' : time(),
            'proof' : -1,
            'index' : cur_index
            }
    json.dumps(dict(data), ensure_ascii=False)

    with open(BLOCKCHAIN_DIR + cur_index + '.json', 'w') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    if make_proof is True:
        get_POW(str(cur_index))


if __name__ == '__main__':
    app.run(debug=True)
