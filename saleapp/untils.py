from saleapp.models import Category, Rule, PhieuNhapSach, ChiTietNhapSach, Product, User, UserRole, SachTacGia, Receipt, \
    ReceiptDetail, Comment, UserReceipt, TacGia, RatingPerson
from flask_login import current_user
from sqlalchemy import func, and_
from saleapp import app, db, model, algorithm
import json
import hashlib
from sqlalchemy.sql import extract
from datetime import timedelta, datetime, date
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd


def read_json(path):
    f = open(path, "r")
    data = json.load(f)
    f.close()

    return data


def load_categories():
    return Category.query.all()
    # return read_json(os.path.join(app.root_path, 'data/categories.json'))


def load_products(cate_id=None, name=None, page=1):
    products = Product.query.filter(Product.active.__eq__(True))

    if cate_id:
        products = products.filter(Product.category_id.__eq__(cate_id))
    if name:
        products = products.filter(Product.name.contains(name))

    page_size = app.config['PAGE_SIZE']
    start = (page - 1) * page_size
    end = start + page_size

    return products.slice(start, end).all()

def process2(df, nhap):  #Nhập một phần gợi ý
    result = cosine_similarity(
        [model.encode(nhap)],
        df['products_embedding'].tolist()
    )
    sort_list = pd.DataFrame(result[0]).sort_values(by = 0, ascending = False)
    similar_items = sort_list.index.tolist()
    similar_items = similar_items[0: ]
    return similar_items


import re
import numpy as np
def load_products2(cate_id=None, name=None, page=1):

    ids = []
    des = []

    for i in load_all_products():
        ids.append(i.id)
        vector_string = (i.vec_description).strip('[]')
        vector_list = vector_string.split()

        vector_list = [float(value) for value in vector_list]
        des.append(vector_list)

    data = pd.DataFrame({'id': id, 'products_embedding': des})

    new_data = process2(data, name)

    # print(new_data[:10])

    final_data = []
    for i in new_data[:8]:
        final_data.append(get_product_by_id(int(i)))

    page_size = app.config['PAGE_SIZE']
    start = (page - 1) * page_size
    end = start + page_size

    return final_data[start:end]


def load_all_products():
    products = Product.query.filter(Product.active.__eq__(True))
    # print(products)
    return products

from surprise import *

def load_recommend_product(id=None):
    # print(algorithm)
    if id:
        products = get_all_product()
        ids = []
        suggest = []
        for i in products:
            est_pro = algorithm.predict(id, i.id).est
            ids.append(i.id)
            suggest.append(est_pro)

        df = pd.DataFrame({'id': ids, 'EstimateScore': suggest})

        all_products = []
        for i, row in df.head(100).sample(12).iterrows():
            all_products.append(get_product_by_id(row['id']))

        return all_products

    else:
        print("else")
        return load_all_products()[:12]



def get_product_by_id(product_id):
    # products = read_json(os.path.join(app.root_path, 'data/products.json'))
    #
    # for p in products:
    #     if p['id'] == product_id:
    #         return p

    products = Product.query.get(product_id)

    return products

def get_cat_id_by_cat_name(name):
    cate = Category.query.filter(Category.name.__eq__(name))

    return cate.id

def get_all_product(k = None):
    p = db.session.query(Product.id, Product.name, Category.name, Product.quantity, Product.price) \
        .filter(Product.category_id.__eq__(Category.id))

    # print(p)
    if k:
        return p.slice(0, k).all()
    return p.all()


def get_product_by_id2(product_id):
    p = p = db.session.query(Product.id, Product.name, Category.name, Product.quantity, Product.price) \
        .filter(Product.category_id.__eq__(Category.id), Product.id.__eq__(product_id))

    # print(p.first())

    return p.first()


def get_rule_value(name):
    return Rule.query.filter(Rule.name.__eq__(name)).first().value


def delete_chi_tiet_nhap_sach_by_id(id):
    p = ChiTietNhapSach.query.filter(ChiTietNhapSach.product_id.__eq__(id)).first()

    if p:
        db.session.delete(p)
        db.session.commit()


def delete_sach_tac_gia_by_id(id):
    p = SachTacGia.query.filter(SachTacGia.product_id.__eq__(id)).all()
    for i in p:
        db.session.delete(i)
        db.session.commit()


def delete_receipt_detail_by_id(id):
    p = ReceiptDetail.query.filter(ReceiptDetail.product_id.__eq__(id)).all()

    for i in p:
        db.session.delete(i)
        db.session.commit()

def delete_comment_by_id(id):
    p = Comment.query.filter(Comment.product_id.__eq__(id)).all()

    for i in p:
        print(i)
        db.session.delete(i)
        db.session.commit()

def delete_product_by_id(id):
    product = Product.query.get(id)

    if product:
        delete_chi_tiet_nhap_sach_by_id(id)
        delete_receipt_detail_by_id(id)
        delete_sach_tac_gia_by_id(id)
        delete_comment_by_id(id)

        db.session.delete(product)
        db.session.commit()


def count_product(category_id=None, kw=None):
    p = Product.query.filter(Product.active.__eq__(True))
    if category_id:
        return p.filter(Product.category_id.__eq__(category_id)).count()
    if kw:
        return p.filter(Product.name.contains(kw)).count()
    return p.count()


def minus_product_quality(id, value):
    product = Product.query.filter(Product.id.__eq__(id)).first()

    product.quantity -= int(value)

    db.session.commit()


def add_user(name, username, password, diachi, **kwargs):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    user = User(name=name.strip(), username=username, password=password, diachi=diachi,
                email=kwargs.get('email'), avatar=kwargs.get('avatar'))

    db.session.add(user)
    db.session.commit()

def add_rating(user_id, product_id, rating):
    rate = RatingPerson(user_id=user_id, product_id=product_id, quantity=rating)

    db.session.add(rate)
    db.session.commit()


def get_date_receipt(id):
    return Receipt.query.filter(Receipt.id.__eq__(id)).first().created_date


def get_user_name(id):
    id = UserReceipt.query.filter(UserReceipt.receipt_id.__eq__(id)).first().user_id

    return User.query.filter(User.id.__eq__(id)).first().name

def check_username(username):
    p = User.query.filter(User.username.__eq__(username)).first()

    return p

def get_time(id):
    receipt = get_date_receipt(id)
    # print(receipt)
    # print(receipt + timedelta(hours=48))
    # print(datetime.now())
    # print(datetime.now() > receipt + timedelta(hours=48))

def get_all_receipt_out_of_date():
    hours = get_rule_value('TIME')
    time = datetime.now() - timedelta(hours=hours)
    print(time)
    p = Receipt.query.filter(Receipt.payment.__eq__(False), (Receipt.created_date < time))

    return p.all()

def get_all_receipt_not_pay(id=None):
    receipt = Receipt.query.filter(Receipt.id.__eq__(id)).first()
    hours = get_rule_value('TIME')

    # print(receipt.created_date)
    # print(datetime.now())
    # print(receipt.created_date + timedelta(hours=48))
    # print(receipt.created_date + timedelta(hours=48) < datetime.now())

    if receipt:
        if receipt.payment == False:
            if (receipt.created_date + timedelta(hours=hours) > datetime.now()):
                p = db.session.query(Product.name, Category.name, ReceiptDetail.quantity, ReceiptDetail.unit_price,
                                     Product.id) \
                    .join(Product, Product.id.__eq__(ReceiptDetail.product_id)) \
                    .filter(
                    and_(
                        ReceiptDetail.receipt_id.__eq__(id)),
                    Category.id.__eq__(Product.category_id),
                )

                # print(p.all())
                return p.all()


def get_receipt_by_id(id):
    p = db.session.query(Product.name, Category.name, ReceiptDetail.quantity, ReceiptDetail.unit_price, Product.id) \
        .join(Product, Product.id.__eq__(ReceiptDetail.product_id)) \
        .filter(
        and_(
            ReceiptDetail.receipt_id.__eq__(id)),
        Category.id.__eq__(Product.category_id)
    )

    # print(p.all())
    return p.all()


def get_total_price_by_id(id):
    p = db.session.query(ReceiptDetail.receipt_id, func.sum(ReceiptDetail.quantity * ReceiptDetail.unit_price)) \
        .filter(ReceiptDetail.receipt_id.__eq__(id)) \
        .group_by(ReceiptDetail.receipt_id)
    return p.first()[1]


def add_phieunhapsach():
    phieu = PhieuNhapSach()
    db.session.add(phieu)
    db.session.commit()

    return phieu


def add_chitietnhapsach(product, phieu, quantity):
    chitet = ChiTietNhapSach(product_id=product.id, phieunhapsach_id=phieu.id, quantity=quantity)

    db.session.add(chitet)
    db.session.commit()
    return chitet


def add_sachtacgia(product, tacgia):
    sactacgia = SachTacGia(product_id=product.id, tacgia_id=tacgia.id)
    db.session.add(sactacgia)
    db.session.commit()

    return sactacgia


def add_product(name, category, author, quantity, mota, avatar, price, **kwargs):
    soluong = get_rule_value('MINIMUM_IMPORT')
    limit = get_rule_value('MINIMUM_LIMIT')

    product = Product.query.filter(Product.name.__eq__(name)).first()
    tacgia = add_author(author)

    if not product:
        cate = add_category(category)

        product = Product(name=name, category_id=cate.id, quantity=quantity, description=mota, image=avatar,
                          price=price)
        db.session.add(product)
        phieu = add_phieunhapsach()
        chitiet = add_chitietnhapsach(product=product, phieu=phieu, quantity=quantity)
        sactacgia = add_sachtacgia(product=product, tacgia=tacgia)

        db.session.commit()

        return 'Nhập thành công'
    else:
        if product.quantity < limit:
            product.quantity += int(quantity)
            sactacgia = add_sachtacgia(product=product, tacgia=tacgia)
            db.session.commit()
            return 'Thêm số lượng thành công'
        else:
            return 'Số lượng trong kho lớn hơn 300'


def add_author(name):
    tacgia = TacGia.query.filter(TacGia.name.__eq__(name)).first()

    if not tacgia:
        tacgia = TacGia(name=name)
        db.session.add(tacgia)
        db.session.commit()

    return tacgia


def add_category(name):
    cate = Category.query.filter(Category.name.__eq__(name)).first()

    if not cate:
        cate = Category(name=name)
        db.session.add(cate)
        db.session.commit()

    return cate


def check_login(username, password, role=UserRole.USER):
    if username and password:
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

        return User.query.filter(User.username.__eq__(username),
                                 User.password.__eq__(password),
                                 User.user_role.__eq__(role)).first()


def check_admin_login(username, password):
    if username and password:
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

        return User.query.filter(User.username.__eq__(username),
                                 User.password.__eq__(password),
                                 User.user_role != UserRole.USER).first()


def get_user_by_id(user_id):
    return User.query.get(user_id)


def category_stats():
    '''
    SELECT c.id, c.name, count(p.id)
    FROM category c left outer join product p on c.id = p.id
    Group by c.name, c.id
    '''

    # return Category.query.join(Product, Product.category_id.__eq__(Category.id)).add_columns(func.count(Product.id)).group_by(Category.id, Category.name).all()
    with app.app_context():
        return db.session.query(Category.id, Category.name, func.count(Product.id)) \
            .join(Product, Product.category_id.__eq__(Category.id), isouter=True) \
            .group_by(Category.id).all()


def products_stats(kw=None, from_date=None, to_date=None):
    p = db.session.query(Product.id, Product.name, func.sum(ReceiptDetail.quantity * ReceiptDetail.unit_price)) \
        .join(ReceiptDetail, ReceiptDetail.product_id.__eq__(Product.id), isouter=True) \
        .join(Receipt, Receipt.id.__eq__(ReceiptDetail.receipt_id)) \
        .group_by(Product.id, Product.name)

    # print(p)

    if kw:
        p = p.filter(Product.name.contains(kw))
    if from_date:
        p = p.filter(Receipt.created_date.__ge__(from_date))
    if to_date:
        p = p.filter(Receipt.created_date.__le__(to_date))

    return p.all()


def change_receipt_payment_by_id(id):
    r = Receipt.query.filter(Receipt.id.__eq__(int(id))).first()

    r.payment = True

    db.session.commit()


def add_receipt(cart, payment=1):
    if cart:
        # receipt = Receipt(user=current_user)
        receipt = Receipt(payment=payment)

        user_receipt = UserReceipt(user=current_user, receipt=receipt)

        db.session.add(receipt)
        db.session.add(user_receipt)

        for c in cart.values():
            d = ReceiptDetail(receipt=receipt,
                              product_id=c['id'],
                              quantity=c['quantity'],
                              unit_price=c['price'])
            db.session.add(d)

    db.session.commit()

    return receipt


def count_cart(cart):
    total_quantity, total_amount = 0, 0

    if cart:
        for c in cart.values():
            total_quantity += c['quantity']
            total_amount += c['quantity'] * c['price']

    return {
        'total_amount': total_amount,
        'total_quantity': total_quantity
    }


def add_comment(content, product_id):
    c = Comment(content=content, product_id=product_id, user=current_user)

    db.session.add(c)
    db.session.commit()

    return c


def get_comments(product_id, page=1):
    page_size = app.config['COMMENT_SIZE']
    start = (page - 1) * page_size
    end = start + page_size

    return Comment.query.filter(Comment.product_id.__eq__(product_id)).order_by(-Comment.id).slice(start,
                                                                                                   start + page_size).all()


def product_month_stats(year):
    p = db.session.query(extract('month', Receipt.created_date),
                         func.sum(ReceiptDetail.quantity * ReceiptDetail.unit_price)) \
        .join(ReceiptDetail, ReceiptDetail.receipt_id.__eq__(Receipt.id)) \
        .filter(extract('year', Receipt.created_date).__eq__(year)) \
        .group_by(extract('month', Receipt.created_date)) \
        .order_by(extract('month', Receipt.created_date))
    # print(p)
    return p.all()


def count_comment(product_id):
    return Comment.query.filter(Comment.product_id.__eq__(product_id)).count()


def total_price_month(month=12):
    p = db.session.query(extract('month', Receipt.created_date),
                         func.sum(ReceiptDetail.quantity * ReceiptDetail.unit_price)) \
        .join(Receipt, Receipt.id.__eq__(ReceiptDetail.receipt_id)) \
        .filter(
        and_(
            extract('month', Receipt.created_date).__eq__(month),
            Receipt.payment.__eq__(1)
        )
    ) \
        .group_by(extract('month', Receipt.created_date)).all()

    print(p)
    return p


def category_month_stats(month=12):
    total = total_price_month(month)

    if total:
        p = db.session.query(Category.name, func.sum(ReceiptDetail.quantity * ReceiptDetail.unit_price),
                             func.sum(ReceiptDetail.quantity),
                             func.round(
                                 func.sum(ReceiptDetail.quantity * ReceiptDetail.unit_price) / total[0][1] * 100), 3) \
            .join(Product, Product.id.__eq__(ReceiptDetail.product_id)) \
            .join(Category, Category.id.__eq__(Product.category_id)) \
            .join(Receipt, Receipt.id.__eq__(ReceiptDetail.receipt_id)) \
            .filter(
            and_(
                extract('month', Receipt.created_date).__eq__(month),
                Receipt.payment.__eq__(1)
            )
        ) \
            .group_by(Category.name)

        print(p)
        return p.all()

    return {}


def total_product_month(month):
    p = db.session.query(extract('month', Receipt.created_date),
                         func.sum(ReceiptDetail.quantity)) \
        .join(Receipt, Receipt.id.__eq__(ReceiptDetail.receipt_id)) \
        .filter(
        and_(
            extract('month', Receipt.created_date).__eq__(month),
            Receipt.payment.__eq__(1)
        )
    ) \
        .group_by(extract('month', Receipt.created_date)).all()

    return p


def product_count_month_stats(month=12):
    total = total_product_month(month)

    if total:
        p = db.session.query(Product.name, Category.name, func.sum(ReceiptDetail.quantity),
                             func.round(func.sum(ReceiptDetail.quantity) / total[0][1] * 100), 3) \
            .join(Product, Product.category_id.__eq__(Category.id)) \
            .join(ReceiptDetail, Product.id.__eq__(ReceiptDetail.product_id)) \
            .join(Receipt, Receipt.id.__eq__(ReceiptDetail.receipt_id)) \
            .filter(
            and_(
                extract('month', Receipt.created_date).__eq__(month),
                Receipt.payment.__eq__(1)
            )
        ) \
            .group_by(Product.name, Category.name)

        print(p)
        return p.all()

    return {}
