from flask import Flask, request, jsonify
import jwt, datetime
from pymongo import MongoClient

from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = "8aacf358ee03b9e906455587c9538669"

client = MongoClient('localhost', 27017)
db = client['user_login']


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split("+")[1].strip()
        if not token:
            return jsonify({"message": "Please Register"})
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])

            current_user = data['email']
        except Exception as e:
            print("exception token", token, e)
            return jsonify({"message": "Please Register"})
        return f(current_user, *args, **kwargs)

    return decorated


@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        if db.users.find({"email": email}).count() > 0:
            return jsonify({"message": "User already exist"})
        db.users.insert_one(
            {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "password": password
            })

    return jsonify({"message": "Registered successfully"})


@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    actual_data = db.users.find_one({'email': email}, {'_id': 0})

    if actual_data != {}:
        if request.form['email'] == actual_data['email'] and request.form['password'] == actual_data['password']:
            token = jwt.encode({'email': request.form['email'], 'password': request.form['password'],
                                'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)},
                               app.config['SECRET_KEY'])

            return jsonify({"Access_token": token.decode()})
        else:
            return jsonify({"message": "Invalid Credentials"})
    else:
        return jsonify({"message": "Please Register"})


@app.route('/template', methods=['POST', 'GET', 'PUT', 'DELETE'])
@token_required
def insert_template(current_user):
    if request.method == 'POST':

        if db.users.find({"email": current_user}).count() > 0:
            db.templates.insert_one(
                {
                    "template_name": request.form['template_name'],
                    "subject": request.form['subject'],
                    "body": request.form["body"],
                    "user": current_user
                })
            return {"message": "Insertion success"}
        return {"message": "Insertion Unsuccessful"}

    if request.method == 'GET':
        temp_id = request.args.get("template_id")
        if temp_id is None:
            cursy = db.templates.find({"user": current_user}, {"user": 0, "_id": 0})
            data_list = [rec for rec in cursy]

            return jsonify({"data": data_list})
        else:
            cursy = db.templates.find({'user':current_user,"template_name": temp_id}, {"user": 0, "_id": 0})
            data_list = [rec for rec in cursy]

            return jsonify({"data": data_list})

    if request.method == 'PUT':
        temp_id = request.args.get("template_id")
        filter = {'user':current_user,'template_name': temp_id}
        newvalues = {"$set": {'subject': request.form['subject'], "body": request.form["body"]}}

        result =db.templates.update_one(filter, newvalues)
        if result.matched_count  > 0:
            return {"message": "Update Success"}
        else:
            return {"message":"Update Unsuccessful"}


    if request.method == 'DELETE':
        temp_id = request.args.get("template_id")
        filter = {'user':current_user,'template_name': temp_id}
        result = db.templates.delete_one(filter)


        if result.deleted_count > 0:
            return {"message": "Delete Success"}
        else:
            return {"message":"Delete Unsuccessful"}


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False)
