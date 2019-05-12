from web_app import db

class meteor_articles(db.Model):
    __tablename__ = 'meteor_articles'

    id = db.Column(db.Integer, primary_key=True)
    art_id = db.Column(db.String())         # <= id
    art_shortid = db.Column(db.String())    # <= shortId, also url
    author_gender = db.Column(db.Integer()) # <= (authorGender=='female')? 0 : 1
    art_author = db.Column(db.String())     # <= authorAlias
    art_school = db.Column(db.String())     # <= authorSchoolName
    art_time = db.Column(db.DateTime())     # <= createdAt
    art_likes = db.Column(db.Integer())     # <= starLength
    art_title = db.Column(db.String())      # <= title
    art_content = db.Column(db.Text())      # <= content

    def __init__(self, id, shortid, gender, author, school, time, likes, title, content):
        self.art_id = id
        self.art_shortid = shortid
        self.author_gender = gender
        self.art_author = author
        self.art_school = school
        self.art_time = time
        self.art_likes = likes
        self.art_title = title
        self.art_content = content

    def __repr__(self):
        return str({
            'art_id': self.art_id,
            'art_shortid': self.art_shortid,
            'author_gender': self.author_gender,
            'art_author': self.art_author,
            'art_school': self.art_school,
            'art_time': self.art_time,
            'art_likes': self.art_likes,
            'art_title': self.art_title,
            'art_content': self.art_content
        })

    def serialize(self):
        return {
            'art_id': self.art_id,
            'art_shortid': self.art_shortid,
            'author_gender': self.author_gender,
            'art_author': self.art_author,
            'art_school': self.art_school,
            'art_time': self.art_time,
            'art_likes': self.art_likes,
            'art_title': self.art_title,
            'art_content': self.art_content
        }

class meteor_comments(db.Model):
    # comment number is according to article api "commentLength" field
    __tablename__ = 'meteor_comments'

    id = db.Column(db.Integer, primary_key=True)
    art_id = db.Column(db.String())
    art_shortid = db.Column(db.String())
    comment_author = db.Column(db.String())
    author_gender = db.Column(db.Integer())
    comment_floor = db.Column(db.Integer())
    comment_time = db.Column(db.DateTime())
    comment_likes = db.Column(db.Integer())
    comment_content = db.Column(db.Text())
    comment_response = db.Column(db.Text())

    def __init__(self, id, shortid, author, gender, floor, time, likes, content, response=""):
        self.art_id = id
        self.art_shortid = shortid
        self.comment_author = author
        self.author_gender = gender
        self.comment_floor = floor
        self.comment_time = time
        self.comment_likes = likes
        self.comment_content = content
        self.comment_response = response

    def __repr__(self):
        return str({
            'art_id': self.art_id,
            'art_shortid': self.art_shortid,
            'comment_author': self.comment_author,
            'author_gender': self.author_gender,
            'comment_floor': self.comment_floor,
            'comment_time': self.comment_time,
            'comment_likes': self.comment_likes,
            'comment_content': self.comment_content,
            'comment_response': self.comment_response
        })

    def serialize(self):
        return {
            'art_id': self.art_id,
            'art_shortid': self.art_shortid,
            'comment_author': self.comment_author,
            'author_gender': self.author_gender,
            'comment_floor': self.comment_floor,
            'comment_time': self.comment_time,
            'comment_likes': self.comment_likes,
            'comment_content': self.comment_content,
            'comment_response': self.comment_response
        }