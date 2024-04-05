import cloudinary.uploader

from saleapp.models import Category, SachTacGia, Product, UserRole, Receipt, Rule, UserReceipt, ChiTietNhapSach, ReceiptDetail, Comment, RatingPerson
from saleapp import app, db, dao, untils
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from flask import request, redirect, jsonify
from datetime import datetime


class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class ChangeRuleView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class RatingView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN

class ProductView(AuthenticatedModelView):
    column_display_pk = True
    can_view_details = True
    can_export = True
    can_create = False
    can_delete = False
    column_searchable_list = ['name', 'description', 'id']
    column_filters = ['name', 'price']
    column_export_list = ['image']
    column_labels = {
        'created_date': 'Ngày tạo',
        'name': 'Tên'
    }
    column_sortable_list = ['name', 'id', 'price']
    column_list = ['id', 'name', 'description', 'price']

    def is_accessible(self):
        return current_user.is_authenticated and not current_user.user_role == UserRole.USER

class ChiTiet(AuthenticatedModelView):
    column_display_pk = True
    can_view_details = True
    can_export = True
    column_searchable_list = ['product_id']

class ReceiptView(AuthenticatedModelView):
    column_display_pk = True
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
    can_export = True
    column_searchable_list = ['id']

    column_filters = ['payment']

    column_sortable_list = ['created_date']


class ChiTietHoaDon(AuthenticatedModelView):
    column_display_pk = True
    can_view_details = True
    can_export = True
    column_searchable_list = ['product_id']

class SachTacGiaView(AuthenticatedModelView):
    column_display_pk = True
    can_view_details = True
    can_export = True
    column_searchable_list = ['product_id']


class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')

    def is_accessible(self):
        return current_user.is_authenticated


class StatsView(BaseView):
    @expose('/')
    def index(self):
        kw = request.args.get('kw')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')

        year = request.args.get('year', '2022')

        month = request.args.get('month', 12)

        month2 = request.args.get('month2', 12)

        return self.render('admin/stats.html',
                           stats=untils.products_stats(
                               kw=kw,
                               from_date=from_date,
                               to_date=to_date),
                           month_stats=untils.product_month_stats(year),
                           cate_stats=untils.category_month_stats(month),
                           total_price_month=untils.total_price_month(month),
                           product_stats=untils.product_count_month_stats(month2),
                           total_product_month=untils.total_product_month(month2))

    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class DeleteView(BaseView):
    @expose('/')
    def index(self):
        id = request.args.get('value')
        pay = request.args.get('payment')

        product = untils.get_product_by_id2(id)

        all_product = untils.get_all_product(k = 20)

        quote = ''

        if id and not product:
            quote = 'Không có sản phẩm hợp lệ!'

        if product:
            return self.render('admin/delete.html', id=id, products=all_product, product=product, pay = pay, quote=quote)
        if pay:
            quote = 'Xóa thành công'
            untils.delete_product_by_id(pay)
            # return redirect('/admin/deleteview')

        return self.render('admin/delete.html', products=all_product, product=product, pay=pay, quote=quote)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class PayView(BaseView):
    @expose('/')
    def __index__(self):

        id = request.args.get('value')
        receipt = untils.get_all_receipt_not_pay(id)
        pay = request.args.get('payment')

        # time = untils.get_time(id)

        out_date = untils.get_all_receipt_out_of_date()
        print(out_date)

        if receipt:
            buyer_name = untils.get_user_name(id)
            date = untils.get_date_receipt(id)
            total = untils.get_total_price_by_id(id)

            return self.render('admin/payment.html', receipt=receipt, user=current_user, name=buyer_name, date=date,
                               total=total, id=id, success=None)

        if pay:
            user_receipt = UserReceipt(user_id=int(current_user.id), receipt_id=int(pay))
            untils.change_receipt_payment_by_id(pay)
            receipt = untils.get_receipt_by_id(pay)

            for i in receipt:
                untils.minus_product_quality(i[4], i[2])

            receipt = None

        return self.render('admin/payment.html', receipt=receipt, user=current_user, success=1, id=id, out_date=out_date, time= datetime.now())

    def is_accessible(self):
        return current_user.is_authenticated and (
                    current_user.user_role == UserRole.ADMIN or current_user.user_role == UserRole.STAFF)


class ImportView(BaseView):
    @expose('/')
    def __index__(self):

        name = request.args.get('name')
        quantity = request.args.get('soluong')
        mota = request.args.get('mota')
        price = request.args.get('gia')
        avatar_path = 'https://cdn.tgdd.vn/Products/Images/42/235838/Galaxy-S22-Ultra-Burgundy-600x600.jpg'

        avatar = request.files.get('avatar')
        if avatar:
            res = cloudinary.uploader.upload(avatar)
            avatar_path = res['secure_url']

        if name:
            category = request.args.get('theloai')
            tacgia = request.args.get('tacgia')

            return self.render('admin/import.html', min=untils.get_rule_value('MINIMUM_IMPORT'),
                               quote=untils.add_product(name=name, category=category, author=tacgia, quantity=quantity,
                                                        price=price, mota=mota, avatar=avatar_path))

        return self.render('admin/import.html', min=untils.get_rule_value('MINIMUM_IMPORT'))

    def is_accessible(self):
        return current_user.is_authenticated and (
                    current_user.user_role == UserRole.ADMIN or current_user.user_role == UserRole.IMPORTER)


class MyAdminIndex(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html', stats=untils.category_stats())



