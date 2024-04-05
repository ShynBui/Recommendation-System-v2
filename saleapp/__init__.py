import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote
import cloudinary
from flask_login import LoginManager
from underthesea import word_tokenize
from sentence_transformers import SentenceTransformer, util
import pandas as pd
import pickle
from surprise import *


app = Flask(__name__)

app.secret_key = '689567gh$^^&*#%^&*^&%^*DFGH^&*&*^*'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost/quanlybansach?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

app.config['PAGE_SIZE'] = 8
app.config['COMMENT_SIZE'] = 8
app.config['PAGE_INF'] = 15

cloudinary.config(
    cloud_name = "dhffue7d7",
    api_key = "215425482852391",
    api_secret = "a9xaGBMJr7KgKhJa-1RpSpx_AmU"
)

model = SentenceTransformer('sentence-transformers/all-MiniLM-L12-v2')


product_rating = pd.read_csv(os.path.join(os.getcwd(), 'data/Products_ThoiTrangNam_rating_raw.csv'), delimiter='\t')
reader = Reader()
data = Dataset.load_from_df(product_rating[['user_id', 'product_id', 'rating']], reader)
algorithm = SVD()

trainset = data.build_full_trainset()
algorithm.fit(trainset)


db = SQLAlchemy(app=app)
login = LoginManager(app=app)






