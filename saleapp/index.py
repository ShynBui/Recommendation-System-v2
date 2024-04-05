import math
import datetime
from flask import render_template, request, redirect, session, jsonify, url_for, flash
from saleapp import app, login, untils
from saleapp.models import UserRole
from flask_login import login_user, logout_user, login_required, current_user
import cloudinary.uploader
from admin import *


@app.route("/")
def home():
    cates = untils.load_categories()
    kw = request.args.get('keyword')
    products = untils.load_products(None, kw)
    if current_user.is_authenticated:
        user_id = int(current_user.id)
    else:
        user_id = None

    return render_template('index.html', categories=cates, kw=kw, products=untils.load_recommend_product(user_id))


@app.route("/products")
def product_list():
    cates = untils.load_categories()

    cate_id = request.args.get('category_id')
    page = int(request.args.get('page', 1))
    kw = request.args.get('keyword', '')
    des = request.args.get('des', '')
    max_page = app.config['PAGE_INF']
    if page > (max_page - 1) / 2:
        start_page = page - (max_page - 1) / 2
        end_page = page + (max_page - 1) / 2
    else:
        start_page = 1
        end_page = max_page
    # print(des)
    products = untils.load_products(cate_id, kw, page=int(page))
    if kw != '':
        products = untils.load_products(cate_id, kw, page=int(page))
    if des != '':
        products = untils.load_products2(cate_id, des, page=int(page))
        count = len(products)

        return render_template('products.html', products=products, cates=cates, kw=kw,
                               pages=math.ceil(count / app.config['PAGE_SIZE']), cate_id=cate_id, page_now=page, start_page=int(start_page), end_page=int(end_page))

    count = untils.count_product(category_id=cate_id, kw=kw)

    # print(count)

    return render_template('products.html', products=products, cates=cates, kw=kw,
                           pages=math.ceil(count / app.config['PAGE_SIZE']), cate_id=cate_id, page_now=page, start_page=int(start_page), end_page=int(end_page))


@app.route("/products/<int:product_id>")
def product_detail(product_id):
    product = untils.get_product_by_id(product_id)

    kw = request.args.get('keyword')
    cates = untils.load_categories()
    page = int(request.args.get('page', 1))

    comments = untils.get_comments(product_id=product_id, page=int(page))
    max_page = app.config['PAGE_INF']
    if page > (max_page - 1) / 2:
        start_page = page - (max_page - 1) / 2
        end_page = page + (max_page - 1) / 2
    else:
        start_page = 1
        end_page = max_page
    if kw:
        count = untils.count_product(kw=kw)
        products = untils.load_products(None, kw, page=int(page))
        return render_template('products.html', products=products, cates=cates, kw=kw,
                               pages=math.ceil(count / app.config['PAGE_SIZE']), page_now=page, start_page=int(start_page), end_page=int(end_page))

    return render_template('product_detail.html', product=product, cates=cates, comments=comments,
                           pages=math.ceil(untils.count_comment(product_id=product_id) / app.config['COMMENT_SIZE']), start_page=int(start_page), end_page=int(end_page))


@app.route('/submit-review', methods=['POST'])
def submit_review():
    product_id = request.form.get('product_id')
    rating = request.form.get('rating')

    untils.add_rating(current_user.id, product_id, rating)

    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/cart')
def cart():
    cates = untils.load_categories()

    cate_id = request.args.get('category_id')
    page = int(request.args.get('page', 1))
    kw = request.args.get('keyword')

    max_page = app.config['PAGE_INF']
    if page > (max_page - 1) / 2:
        start_page = page - (max_page - 1) / 2
        end_page = page + (max_page - 1) / 2
    else:
        start_page = 1
        end_page = max_page

    if kw:
        count = untils.count_product(kw=kw)
        products = untils.load_products(None, kw, page=int(page))
        return render_template('products.html', products=products, cates=cates, kw=kw,
                               pages=math.ceil(count / app.config['PAGE_SIZE']), page_now=page, start_page=int(start_page), end_page=int(end_page))

    return render_template('cart.html', stats=untils.count_cart(session.get(cart)))


@app.route('/api/add-cart', methods=['post'])
def add_to_cart():
    data = request.json
    id = str(data.get('id'))
    name = data.get('name')
    price = data.get('price')

    # import pdb
    # pdb.set_trace()

    cart = session.get('cart')
    if not cart:
        cart = {}

    if id in cart:
        cart[id]['quantity'] += 1
    else:
        cart[id] = {
            'id': id,
            'name': name,
            'price': price,
            'quantity': 1
        }

    session['cart'] = cart

    return jsonify(untils.count_cart(cart))


@app.route('/api/update-cart', methods=['put'])
def update_cart():
    data = request.json
    id = str(data.get('id'))
    quantity = data.get('quantity')

    cart = session.get('cart')

    if cart and id in cart:
        cart[id]['quantity'] = quantity
        session['cart'] = cart

    return jsonify(untils.count_cart(cart))


@app.route('/api/delete-cart/<product_id>', methods=['delete'])
def delete_cart(product_id):
    cart = session.get('cart')

    if cart and product_id in cart:
        del cart[product_id]
        session['cart'] = cart

    return jsonify(untils.count_cart(cart))


@app.route('/api/comments', methods=['post'])
def add_comment():
    data = request.json
    content = data.get('content')
    product_id = data.get('product_id')

    try:
        c = untils.add_comment(content=content, product_id=product_id)
    except:
        return {'status': 404, 'err_msg': "Chuong trinh ban"}

    return {
        'status': 201,
        'comment': {
            'id': c.id,
            'content': c.content,
            'created_date': c.created_date,
            'user': {
                'username': current_user.username,
                'avatar': current_user.avatar
            }
        }
    }


@app.route('/api/pay', methods=['post'])
def pay():
    cart = session.get('cart')

    for i in cart.values():
        untils.minus_product_quality(i['id'], i['quantity'])

    try:
        untils.add_receipt(session.get('cart'))
        del session['cart']
    except:
        return jsonify({'code': 400})

    return jsonify({'code': 200})


@app.route('/api/pay2', methods=['post'])
def pay2():
    try:
        receipt = untils.add_receipt(session.get('cart'), payment=0)
        del session['cart']
    except:
        return jsonify({'code': 400})

    return jsonify({'code': 200,
                    'receipt': receipt.id,
                    'time': untils.get_rule_value('TIME')})


@app.route('/register', methods=['get', 'post'])
def user_register():
    err_msg = ""

    cates = untils.load_categories()

    cate_id = request.args.get('category_id')
    page = int(request.args.get('page', 1))
    kw = request.args.get('keyword')

    max_page = app.config['PAGE_INF']
    if page > (max_page - 1) / 2:
        start_page = page - (max_page - 1) / 2
        end_page = page + (max_page - 1) / 2
    else:
        start_page = 1
        end_page = max_page

    if kw:
        count = untils.count_product(kw=kw)
        products = untils.load_products(None, kw, page=int(page))
        return render_template('products.html', products=products, cates=cates, kw=kw,
                               pages=math.ceil(count / app.config['PAGE_SIZE']), page_now=page, start_page=int(start_page), end_page=int(end_page))

    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        diachi = request.form.get('diachi')
        confirm = request.form.get('confirm')
        avatar_path = None

        if untils.check_username(username):
            err_msg = 'Tài khoản đã tòn tại'
            return render_template('register.html', err_msg=err_msg, cates=cates)

    try:
        if str(password) == str(confirm):
            avatar = request.files.get('avatar')
            if avatar:
                res = cloudinary.uploader.upload(avatar)
                avatar_path = res['secure_url']

            untils.add_user(name=name,
                            username=username,
                            password=password,
                            diachi=diachi,
                            email=email,
                            avatar=avatar_path)
            return redirect(url_for('user_signin'))
        else:
            err_msg = "Mat khau khong khop"
            # print(err_msg)
    except Exception as ex:
        pass
        # err_msg = 'He thong ban' + str(ex)
        # print(err_msg)

    cates = untils.load_categories()
    return render_template('register.html', err_msg=err_msg, cates=cates)


@app.route('/user-login', methods=['get', 'post'])
def user_signin():
    err_msg = ""

    cates = untils.load_categories()

    cate_id = request.args.get('category_id')
    page = int(request.args.get('page', 1))
    kw = request.args.get('keyword')

    max_page = app.config['PAGE_INF']
    if page > (max_page - 1) / 2:
        start_page = page - (max_page - 1) / 2
        end_page = page + (max_page - 1) / 2
    else:
        start_page = 1
        end_page = max_page

    if kw:
        count = untils.count_product(kw=kw)
        products = untils.load_products(None, kw, page=int(page))
        return render_template('products.html', products=products, cates=cates, kw=kw,
                               pages=math.ceil(count / app.config['PAGE_SIZE']), page_now=page, start_page=int(start_page), end_page=int(end_page))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = untils.check_login(username=username, password=password)
        if user:
            login_user(user=user)
            next = request.args.get('next', 'product_list')
            return redirect(url_for(next))
        else:
            err_msg = "Sai tên đăng nhập hoặc mật khẩu"

    return render_template('login.html', err_msg=err_msg)


@app.route('/admin-login', methods=['post'])
def signin_admin():
    username = request.form.get('username')
    password = request.form.get('password')

    # user = untils.check_login(username=username, password=password, role=UserRole.ADMIN)
    user = untils.check_admin_login(username=username, password=password)
    if user:
        # print(1)
        login_user(user=user)

    return redirect('/admin')


@app.route('/user-logout')
def user_signout():
    logout_user()
    session['cart'] = 0
    return redirect(url_for('home'))


@login.user_loader
def user_load(user_id):
    return untils.get_user_by_id(user_id=user_id)


@app.context_processor
def common_response():
    return {
        'cates': untils.load_categories(),
        'cart_stats': untils.count_cart(session.get('cart'))
    }


admin = Admin(app=app, name='QUẢN TRỊ BÁN HÀNG', template_mode='bootstrap4',
              index_view=MyAdminIndex())

# admin.add_view(ChiTiet(ChiTietNhapSach, db.session))
# admin.add_view(ChiTietHoaDon(ReceiptDetail, db.session))
# admin.add_view(SachTacGiaView(SachTacGia, db.session))
admin.add_view(ProductView(Product, db.session))
admin.add_view(StatsView(name='Stats'))
admin.add_view(DeleteView(name='Delete'))
admin.add_view(ImportView(name='Import'))
admin.add_view(ReceiptView(Receipt, db.session))
admin.add_view(PayView(name='Payment'))
admin.add_view(ChangeRuleView(Rule, db.session))
admin.add_view(RatingView(RatingPerson, db.session))
admin.add_view(LogoutView(name='Logout'))

if __name__ == '__main__':
    app.run(debug=True)
