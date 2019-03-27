from web_app import db

class dcard_article(db.Model):
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    art_id = db.Column(db.Integer())        # <= id
    art_gender = db.Column(db.Integer())    # <= (gender=='F')? 0 : 1
    art_owner = db.Column(db.String())      # <= (anonymousSchool)? 'anonymous' : (anonymousDepartment)? school : school+department
    art_time = db.Column(db.DateTime())     # <= createdAt
    art_title = db.Column(db.String())      # <= title
    art_content = db.Column(db.Text())      # <= content

    def __init__(self, id, gender, owner, time, title, content):
        self.art_id = id
        self.art_gender = gender
        self.art_owner = owner
        self.art_time = time
        self.art_title = title
        self.art_content = content

    def __repr__(self):
        return str({
            'art_id': self.art_id,
            'art_gender': self.art_gender,
            'art_owner': self.art_owner,
            'art_time': self.art_time,
            'art_title': self.art_title,
            'art_content': self.art_content
        })

    def serialize(self):
        return {
            'article_id': self.art_id,
            'gender': self.art_gender,
            'owner': self.art_owner,
            'time': self.art_time,
            'title': self.art_title,
            'content': self.art_content
        }

class dcard_comment(db.Model):
    # comment number is according to article api "commentCount" field
    __tablename__ = 'comment'

    id = db.Column(db.Integer, primary_key=True)
    art_id = db.Column(db.Integer())           # <= postId
    comment_owner = db.Column(db.String())     # <= (host)? 'art_owner' : (anonymous)? school : school+department
    owner_gender = db.Column(db.Integer())     # <= (gender=='F')? 0 : 1
    comment_floor = db.Column(db.Integer())    # <= floor
    comment_time = db.Column(db.DateTime())    # <= updatedAt
    comment_content = db.Column(db.Text())     # <= content

    def __init__(self, id, owner, gender, floor, time, content):
        self.art_id = id
        self.comment_owner = owner
        self.owner_gender = gender
        self.comment_floor = floor
        self.comment_time = time
        self.comment_content = content

    def __repr__(self):
        return str({
            'art_id': self.art_id,
            'comment_owner': self.comment_owner,
            'owner_gender': self.owner_gender,
            'comment_floor': self.comment_floor,
            'comment_time': self.comment_time,
            'comment_content': self.comment_content
        })

    def serialize(self):
        return {
            'article_id': self.art_id,
            'comment_owner': self.comment_owner,
            'owner_gender': self.owner_gender,
            'floor': self.comment_floor,
            'time': self.comment_time,
            'content': self.comment_content
        }