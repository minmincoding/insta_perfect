from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient

import hashlib,datetime,jwt

client = MongoClient('mongodb+srv://test:sparta@cluster0.avef3.mongodb.net/Cluster0?retryWrites=true&w=majority')
db = client.instaperfect

app = Flask(__name__)

SECRET_KEY = 'insta'

@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"uid": payload['uid']})
        user = user_info['uid']
        print(user)
        return render_template('feed.html',user=user)

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login"),user=user )
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login") , user=user)

@app.route('/<uid>', methods=['GET'])
def profiles(uid):
    payload = jwt.decode(request.cookies.get('mytoken'), SECRET_KEY, algorithms=['HS256'])
    userid = payload['uid']
    user = db.user.find_one({'uid': uid}, {'_id': False})
    name = user['name']
    hobby = user['hobby']
    profile_desc = user['profile_desc']
    user_photo = user['pr_photo']
    all_feed = db.feed.find({'write_id' : uid}).sort("feed_number", -1)
    write_count = db.feed.count_documents({'write_id': uid})
    return render_template('profile.html',all_feed=all_feed, username=uid, write_count=write_count, userid=userid, user_photo=user_photo, name=name, hobby=hobby, profile_desc=profile_desc)

# 유저 정보 보내주기
@app.route('/user', methods=['GET', 'POST'])
def find_userdb():
    if request.method == 'POST':
        receive_uid = request.form['give_uid']
        find_user = db.user.find_one({'uid': receive_uid}, {'_id': False})
        return jsonify({'response': 'success', 'find_user': find_user})

    payload = jwt.decode(request.cookies.get('mytoken'), SECRET_KEY, algorithms=['HS256'])
    uid_get = db.user.find_one({'uid': payload['uid']})
    uid = uid_get['uid']
    user = db.user.find_one({'uid': uid}, {'_id': False})
    return jsonify({'response': 'success', 'user': user})


# 피드 불러오기
@app.route('/feed', methods=['GET', 'POST'])
def find_feed():
    if request.method == 'POST':
        feed_number = request.form['feed_number']
        find_feed = db.feed.find_one({'feed_number': int(feed_number)}, {'_id': False})
        find_user = db.user.find_one({'uid': find_feed['write_id']}, {'_id': False})
        return jsonify({'response': 'success', 'find_feed': find_feed, 'find_user': find_user})

    payload = jwt.decode(request.cookies.get('mytoken'), SECRET_KEY, algorithms=['HS256'])
    uid_get = db.user.find_one({'uid': payload['uid']})
    uid = uid_get['uid']
    content = list(db.feed.find({'write_id': uid}, {'_id': False}))
    user = db.user.find_one({'uid': uid}, {'_id': False})
    pr_photo = user['pr_photo']
    return jsonify({'response': 'success', 'content': content, 'pr_photo': pr_photo})


# 댓글 입력 저장 후 전송
@app.route('/comment', methods=['GET', 'POST'])
def update_comment():
    payload = jwt.decode(request.cookies.get('mytoken'), SECRET_KEY, algorithms=['HS256'])
    uid_get = db.user.find_one({'uid': payload['uid']})
    uid = uid_get['uid']

    receive_feed_number = request.form['give_feed_number']
    receive_comment = request.form['give_comment']
    db.feed.update_one({'feed_number': int(receive_feed_number)}, {'$push': {'comment': {'write_id': uid, 'text': receive_comment}}})
    pr_photo = uid_get['pr_photo']
    return jsonify({'response': 'success', 'pr_photo': pr_photo, 'write_id': uid, 'text': receive_comment})


@app.route('/login')
def login():
    return render_template('login.html')


@app.route("/join_page")
def join_page():
    return render_template('join.html')


@app.route("/join", methods=["POST"])
def join_post():
    uid_receive = request.form['uid_give']
    name_receive = request.form['name_give']
    pwd_receive = request.form['pwd_give']
    hashed_pw = hashlib.sha256(pwd_receive.encode('utf-8')).hexdigest()


    doc = {
        'uid': uid_receive,
        'name': name_receive,
        'pwd': hashed_pw,
        'pr_photo' : '../static/pr_img/basic.jpg',
        'hobby' : '',
        'profile_desc' : '',
    }

    follow = {

        'uid': uid_receive,
        'follow': [],
        'following': []
    }

    db.user.insert_one(doc)
    db.follow.insert_one(follow)

    return jsonify({'response': 'success', 'msg': '환영합니다!'})

@app.route('/login_check', methods=['POST'])
def login_check():
    uid_receive = request.form['uid_give']
    pwd_receive = request.form['pwd_give']

    pwd_hash = hashlib.sha256(pwd_receive.encode('utf-8')).hexdigest()
    result = db.user.find_one({
        'uid': uid_receive,
        'pwd': pwd_hash
    })

    if result is not None:
        payload = {
            'uid': uid_receive,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        print("token =", end=""), print(token)
        return jsonify({'result': 'success', 'token': token})

    else:
        return jsonify({'result': 'fail', 'msg': 'wrong'})


@app.route('/login/name', methods=['GET'])
def login_name():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        userinfo = db.user.find_one({'uid': payload['uid']})
        return jsonify({'result': 'success', 'name': userinfo['name']})
    except jwt.ExpiredSignatureError:
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})

# 프로필 페이지 이동
@app.route('/profile')
def profile():
    payload = jwt.decode(request.cookies.get('mytoken'), SECRET_KEY, algorithms=['HS256'])
    uid_get = db.user.find_one({'uid': payload['uid']})
    uid = uid_get['uid']
    name = uid_get['name']
    write_count = db.feed.count_documents({'write_id': uid})
    pr_photo = uid_get['pr_photo']
    print(pr_photo)
    #피드 콜렉션에 모든 내용을 받아온다! #feed number로 내림차순 정렬
    all_feed = db.feed.find({'write_id' : uid}).sort("feed_number", -1)

    return render_template('profile.html',all_feed=all_feed, pr_photo=pr_photo, write_count=write_count, username=uid, name=name)

# 이미지 파일 업로드
@app.route('/upload', methods=['GET', 'POST'])
def get_file():
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    if request.method == 'POST':
        image = request.files['file']
        content = request.form['content']
        uid_get = db.user.find_one({'uid': payload['uid']})
        uid = uid_get['uid']
        col = db.feed
        number = col.count_documents({})
        image.save(f'./static/img_upload/{number}.jpg')

        doc = {
            'feed_number' : number + 1,
            'write_id' : uid,
            'photo' : str(number) + '.jpg',
            'content' : content,
            'like_count': 0
        }

        db.feed.insert_one(doc)

    return redirect(url_for('profile'))

@app.route('/feed_number', methods=['GET', 'POST'])
def feed_number():
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    if request.method == 'POST':
        feed_number = request.form['feed_number']
        uid_get = db.user.find_one({'uid': payload['uid']})
        uid = uid_get['uid']
        serch_content = db.feed.find_one({"feed_number": int(feed_number)},{"_id": 0})
        write_id = serch_content['write_id']
        like_count = serch_content['like_count']
        photo = serch_content['photo']
        content = serch_content['content']

        try:
            like_list = serch_content['like_list']
        except:
            like_list = []
        if len(like_list) < 0:
            like = 0
        elif len(like_list) > 1 and uid in like_list:
            like = 1
        else:
            like = 0
        return jsonify({'result': 'success', 'photo': photo, 'content': content, 'username': uid, 'like_count' : like_count, 'write_id': write_id, 'like': like, 'feed_number': feed_number, 'uid':uid})

@app.route('/like_count', methods=['GET', 'POST'])
def like_count():
    payload = jwt.decode(request.cookies.get('mytoken'), SECRET_KEY, algorithms=['HS256'])
    uid = payload['uid']
    if request.method == 'POST':
        number = request.form['feed_number']
        like = request.form['like']
        serch = db.feed.find_one({"feed_number": int(number)},{"_id": 0})
        count = serch['like_count']

        if like == '0':
            try:
                db.feed.update_one({'feed_number': int(number)}, {"$pull": {'like_list' : uid}})
                if count > 1:
                    addcount = count - 1
                    db.feed.update_one({'feed_number': int(number)}, {'$set': {'like_count': addcount}})
                else:
                    pass
                print('빠져나왔당!')
            except:
                pass
        else:
            print(uid,'들어갔당!')
            addcount = count + 1
            db.feed.update_one({'feed_number': int(number)}, {"$push": {'like_list' : uid}},upsert=True)
            db.feed.update_one({'feed_number': int(number)}, {'$set': {'like_count': addcount}})
        
        return jsonify({'result': 'success', 'msg' : '잘 받았다 이눔아!', 'count' : addcount})

@app.route('/pr_edit', methods=['POST', 'GET'])
def pr_edit():
    if request.method == 'POST':
        username = request.form['uid']
        uid_get = db.user.find_one({'uid': username })
        hobby = request.form['hobby']
        description = request.form['description']
        db.user.update_one({'uid': username}, {'$set': {'hobby': hobby}})
        db.user.update_one({'uid': username}, {'$set': {'profile_desc': description}})

    return redirect("/" + username)

@app.route('/pr_upload', methods=['POST', 'GET'])
def pr_upload():
    payload = jwt.decode(request.cookies.get('mytoken'), SECRET_KEY, algorithms=['HS256'])
    uid = payload['uid']
    if request.method == 'POST':    
        image = request.files['file']
        image.save(f'./static/pr_img/{uid}.jpg')
        db.user.update_one({'uid': uid}, {'$set': {'pr_photo': f'./static/pr_img/{uid}.jpg'}})

        return redirect("/" + uid)

        print(photo, content)
        return jsonify({'result': 'success', 'photo': photo, 'content': content, 'username': uid, 'like_count' : like_count})

#  팔로우 부분 db에 저장하기
@app.route("/follow_check", methods=["POST"])
def follow_user():

    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    uid_get = db.user.find_one({'uid': payload['uid']})
    uid = uid_get['uid']

    db.follow.update_one({'uid': "test1234"}, {'$push': {'following': "test45678"}}, upsert=True)
    db.follow.update_one({'uid': "test45678"}, {'$push': {'follow': uid}}, upsert=True)
    return jsonify({'response': 'success'})

# 팔로우 db remove
@app.route("/follow_delete", methods=["POST"])
def follow_delete():
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    uid_get = db.user.find_one({'uid': payload['uid']})
    uid = uid_get['uid']

    db.follow.update_one({"uid": "test45678"}, {'$pull': {"follow": uid}})
    return jsonify({'response': 'success'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)

