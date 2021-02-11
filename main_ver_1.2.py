from flask import Flask, request, jsonify
import jwt, datetime
import pymongo

from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = "8aacf358ee03b9e906455587c9538669"


client = pymongo.MongoClient("mongodb+srv://kiran:kiran123@cluster0.w58py.mongodb.net/user_login?retryWrites=true&w=majority")
db = client.user_login

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split("+")[1].strip()
        if not token:
            return jsonify({"message": "Please Register"}),401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])

            current_user = data['email']
        except Exception as e:
            print("exception token",  e)
            return jsonify({"message": str(e)}),401
        return f(current_user, *args, **kwargs)

    return decorated


@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        val = request.get_json()
        first_name = val['first_name']
        last_name = val['last_name']
        email = val['email']
        password = val['password']
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
    val = request.get_json()
    email = val['email']
    actual_data = db.users.find_one({'email': email}, {'_id': 0})

    if actual_data is not None:
        if val['email'] == actual_data['email'] and val['password'] == actual_data['password']:
            token = jwt.encode({'email': val['email'], 'password': val['password'],
                                'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)},
                               app.config['SECRET_KEY'])

            return jsonify({"Access_token": token.decode()})
        else:
            return jsonify({"message": "Invalid Credentials"}),401
    else:
        return jsonify({"message": "Please Register"}),401


@app.route('/template', methods=['POST', 'GET', 'PUT', 'DELETE'])
@token_required
def insert_template(current_user):
    val = request.get_json()
    if request.method == 'POST':

        if db.users.find({"email": current_user}).count() > 0:
            db.templates.insert_one(
                {
                    "template_name": val['template_name'],
                    "subject": val['subject'],
                    "body": val["body"],
                    "user": current_user
                })
            return jsonify({"message": "Insertion success"}),401
        return jsonify({"message": "Insertion Unsuccessful"}),401

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
        newvalues = {"$set": {'subject': val['subject'], "body": val["body"]}}

        result =db.templates.update_one(filter, newvalues)
        if result.modified_count  > 0:
            return jsonify({"message": "Update Success"}),401
        else:
            return jsonify({"message":"Update Unsuccessful"}),401


    if request.method == 'DELETE':
        temp_id = request.args.get("template_id")
        filter = {'user':current_user,'template_name': temp_id}
        result = db.templates.delete_one(filter)


        if result.deleted_count > 0:
            return jsonify({"message": "Delete Success"}),401
        else:
            return jsonify({"message":"Delete Unsuccessful"}),401


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False)
