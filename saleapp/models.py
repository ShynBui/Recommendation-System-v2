from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship, backref
from saleapp import db, app
from datetime import datetime
from enum import Enum as UserEnum
from flask_login import UserMixin
import os
import hashlib
import pandas as pd
import numpy as np


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)


class UserRole(UserEnum):
    ADMIN = 1
    USER = 2
    STAFF = 3
    IMPORTER = 4


class User(BaseModel, UserMixin):
    __tablename__ = 'user'
    __table_args__ = {'extend_existing': True}
    name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    avatar = Column(String(100), default='https://t3.ftcdn.net/jpg/03/58/90/78/360_F_358907879_Vdu96gF4XVhjCZxN2kCG0THTsSQi8IhT.jpg')
    email = Column(String(50))
    active = Column(Boolean, default=True)
    joined_date = Column(DateTime, default=datetime.now())
    diachi = Column(String(100), nullable=False)
    user_role = Column(Enum(UserRole), default=UserRole.USER)
    comment = relationship('Comment', backref='user', lazy=True)
    user_receipt = relationship('UserReceipt', backref='user', lazy=True)


    def __str__(self):
        return self.name


class Category(BaseModel):
    __tablename__ = 'category'
    __table_args__ = {'extend_existing': True}
    name = Column(String(50), nullable=False)
    products = relationship('Product', backref='category', lazy=True)

    def __str___(self):
        return self.name


class Product(BaseModel):
    __tablename__ = 'product'
    # __table_args__ = {'extend_existing': True}
    name = Column(Text, nullable=False)
    description = Column(Text)
    vec_description = Column(Text)
    price = Column(Float, default=0)
    image = Column(Text)
    active = Column(Boolean, default=True)
    quantity = Column(Integer, default=0)
    rating = Column(Integer, default=0)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)
    created_date = Column(DateTime, default=datetime.now())
    receipt_details = relationship('ReceiptDetail', backref='product', lazy=True)
    comments = relationship('Comment', backref='product', lazy=True)
    sach_tacgia = relationship('SachTacGia', backref='product', lazy=True)
    chitietnhapsach = relationship('ChiTietNhapSach', backref='product', lazy=True)
    rating_person = relationship('RatingPerson', backref='product', lazy=True)

    __table_args__ = {'extend_existing': True}
    def __str___(self):
        return self.name

class Note(BaseModel):
    __abstract__ = True
    # __table_args__ = {'extend_existing': True}
    created_date = Column(DateTime, default= datetime.now())

    def __str___(self):
        return self.created_date

class Receipt(Note):
    __tablename__ = 'receipt'
    # __table_args__ = {'extend_existing': True}
    details = relationship('ReceiptDetail', backref='receipt', lazy=True)
    user_receipt = relationship('UserReceipt', backref='receipt', lazy=True)
    payment = Column(Boolean, default=True)

    __table_args__ = {'extend_existing': True}
    def __str___(self):
        return self.created_date

class UserReceipt(db.Model):
    user_id = Column(Integer, ForeignKey(User.id), nullable=False, primary_key=True)
    receipt_id = Column(Integer, ForeignKey(Receipt.id), nullable=False, primary_key=True)

    __table_args__ = {'extend_existing': True}

class PhieuNhapSach(Note):
    __tablename__ = 'phieunhapsach'
    chitietnhapsach = relationship('ChiTietNhapSach', backref='phieunhapsach', lazy=True)

    __table_args__ = {'extend_existing': True}
    def __str___(self):
        return self.created_date


class ReceiptDetail(db.Model):
    __tablename__ = 'receiptdetail'
    __table_args__ = {'extend_existing': True}
    receipt_id = Column(Integer, ForeignKey(Receipt.id), nullable=False, primary_key=True)
    product_id = Column(Integer, ForeignKey(Product.id), nullable=False, primary_key=True)
    quantity = Column(Integer, default=0)
    unit_price = Column(Float, default=0)


class ChiTietNhapSach(db.Model):
    __tablename__ = 'chitietnhapsach'
    quantity = Column(Integer, default=0)
    product_id = Column(Integer, ForeignKey(Product.id), nullable=False, primary_key=True)
    phieunhapsach_id = Column(Integer, ForeignKey(PhieuNhapSach.id), nullable=False, primary_key=True)

    __table_args__ = {'extend_existing': True}

class Comment(BaseModel):
    content = Column(String(255), nullable = False)
    product_id = Column(Integer, ForeignKey(Product.id), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    created_date = Column(DateTime, default=datetime.now())

    __table_args__ = {'extend_existing': True}
    def __str___(self):
        return self.content


class TacGia(BaseModel):
    name = Column(String(100), nullable=False)
    sach_tacgia = relationship('SachTacGia', backref='tacgia', lazy=True)

    __table_args__ = {'extend_existing': True}
    def __str___(self):
        return self.name


class SachTacGia(db.Model):
    tacgia_id = Column(Integer, ForeignKey(TacGia.id), nullable=False, primary_key=True)
    product_id = Column(Integer, ForeignKey(Product.id), nullable=False, primary_key=True)

    __table_args__ = {'extend_existing': True}

class RatingPerson(db.Model):
    user_id = Column(Integer, ForeignKey(User.id), nullable=False, primary_key=True)
    product_id = Column(Integer, ForeignKey(Product.id), nullable=False, primary_key=True)
    quantity = Column(Integer, default=0)

    __table_args__ = {'extend_existing': True}

class Rule(BaseModel):
    name = Column(String(100), nullable=False, unique=True)
    value = Column(Integer, nullable=False)
    description = Column(Text)

    __table_args__ = {'extend_existing': True}


def get_cat_id_by_cat_name(name):
    cate = Category.query.filter(Category.name.__eq__(name))

    return cate.first().id

if __name__ == '__main__':
    with app.app_context():

        # db.drop_all()
        # db.session.commit()
        db.create_all()
        #
        db.session.commit()
        # #
        #

        data = pd.read_csv(os.path.join(os.getcwd(), 'data/Products_ThoiTrangNam_raw_0.csv'))
        for i in range(1, 9):
            pd.concat([data, pd.read_csv(os.path.join(os.getcwd(), f'data/Products_ThoiTrangNam_raw_{i}.csv'))])

        # data = pd.read_csv(os.path.join(os.getcwd(), 'data/Products_ThoiTrangNam_raw.csv'))[:]

        all_user = pd.read_csv(os.path.join(os.getcwd(), 'data/Products_ThoiTrangNam_rating_raw.csv'), delimiter='\t')

        # user_names = all_user['user'].unique()

        # print(len(user_names))


        # for i in user_names:
        #     password = str(hashlib.md5('1'.strip().encode('utf-8')).hexdigest())
        #     user = User(id= all_user[all_user['user'] == i]['user_id'].iloc[0],name=i.strip(), username= i, password=password, diachi='VietNam')
        #     db.session.add(user)
        #     db.session.commit()

        user_id_mapping = all_user.head(50).groupby('user')['user_id'].first().to_dict()

        print(len(user_id_mapping))

        for username, user_id in user_id_mapping.items():
            password = hashlib.md5('1'.strip().encode('utf-8')).hexdigest()
            user = User(id=user_id, name=username.strip(), username=username, password=password, diachi='VietNam')
            db.session.add(user)
            db.session.commit()

        password = str(hashlib.md5('1'.strip().encode('utf-8')).hexdigest())
        user = User(name="Bùi Tiến Phát", username="u1",
                    password=password, diachi='VietNam', user_role=UserRole.ADMIN)
        db.session.add(user)
        db.session.commit()


        cate = data['sub_category'].unique()
        # print(cate)

        tacgia = TacGia(name="Bùi Tiến Phát")
        db.session.add(tacgia)
        db.session.commit()

        for i in cate:
            c = Category(name=i)
            db.session.add(c)
            db.session.commit()


        for i, row in data.iterrows():
            new_image = row['image']
            if pd.isnull(row['image']):
                new_image = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRtSO-CeaFQtYp7KoBljVRrHXUM6wYg9mmy8oT9B0YmZw&s"
            new_price = row['price']
            if pd.isnull(row['price']):  # Kiểm tra xem giá trị 'price' có là 'nan' không
                new_price = 0.0
            new_des = row['description']
            if pd.isnull(row['description']):  # Kiểm tra xem giá trị 'price' có là 'nan' không
                new_des = ''
            c = Product(name=row['product_name'], description= new_des, price=int(new_price), quantity= np.random.randint(1, 200),
                        category_id= get_cat_id_by_cat_name(row['sub_category']), image= new_image, rating=row['rating'], vec_description=row['description_wt'])
            db.session.add(c)
            db.session.commit()

        rule1 = Rule(name="MINIMUM_IMPORT", value = 100)
        rule2 = Rule(name="TIME", value= 48)
        rule3 = Rule(name="MINIMUM_LIMIT", value= 500)

        db.session.add_all([rule1, rule2, rule3])
        db.session.commit()

