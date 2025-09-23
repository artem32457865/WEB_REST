from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from settings import Session
from models import Menu, Order, OrderStatus

bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(func):
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            flash("Доступ заборонено. Потрібні права адміністратора", "error")
            return redirect(url_for("index"))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    with Session() as session:

        total_orders = session.query(Order).count()
        pending_orders = session.query(Order).filter(Order.status == OrderStatus.PENDING).count()
        active_menu_items = session.query(Menu).filter(Menu.active == True).count()
        
        return render_template("admin/dashboard.html", 
                             total_orders=total_orders,
                             pending_orders=pending_orders,
                             active_menu_items=active_menu_items)

@bp.route("/menu")
@login_required
@admin_required
def menu_management():
    with Session() as session:
        menu_items = session.query(Menu).all()
        return render_template("admin/menu.html", menu_items=menu_items)

@bp.route("/menu/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_menu_item():
    if request.method == "POST":
        name = request.form.get("name")
        price = float(request.form.get("price"))
        description = request.form.get("description")
        category = request.form.get("category")
        image_path = request.form.get("image_path", "")
        
        new_item = Menu(
            name=name,
            price=price,
            description=description,
            category=category,
            image_path=image_path
        )
        
        with Session() as session:
            session.add(new_item)
            session.commit()
        
        flash("Страву додано успішно!", "success")
        return redirect(url_for("admin.menu_management"))
    
    return render_template("admin/add_menu.html")

@bp.route("/menu/edit/<int:item_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_menu_item(item_id):
    with Session() as session:
        item = session.query(Menu).filter(Menu.id == item_id).first()
        
        if not item:
            flash("Страву не знайдено", "error")
            return redirect(url_for("admin.menu_management"))
        
        if request.method == "POST":
            item.name = request.form.get("name")
            item.price = float(request.form.get("price"))
            item.description = request.form.get("description")
            item.category = request.form.get("category")
            item.image_path = request.form.get("image_path", "")
            item.active = bool(request.form.get("active"))
            
            session.commit()
            flash("Страву оновлено успішно!", "success")
            return redirect(url_for("admin.menu_management"))
        
        return render_template("admin/edit_menu.html", item=item)

@bp.route("/menu/delete/<int:item_id>")
@login_required
@admin_required
def delete_menu_item(item_id):
    with Session() as session:
        item = session.query(Menu).filter(Menu.id == item_id).first()
        
        if item:
            session.delete(item)
            session.commit()
            flash("Страву видалено успішно!", "success")
        else:
            flash("Страву не знайдено", "error")
    
    return redirect(url_for("admin.menu_management"))

@bp.route("/orders")
@login_required
@admin_required
def orders_management():
    with Session() as session:
        orders = session.query(Order).order_by(Order.created_at.desc()).all()
        return render_template("admin/orders.html", orders=orders, OrderStatus=OrderStatus)

@bp.route("/orders/update_status/<int:order_id>", methods=["POST"])
@login_required
@admin_required
def update_order_status(order_id):
    new_status = request.form.get("status")
    
    with Session() as session:
        order = session.query(Order).filter(Order.id == order_id).first()
        
        if order and new_status in [status.name for status in OrderStatus]:
            order.status = OrderStatus[new_status]
            session.commit()
            flash("Статус замовлення оновлено!", "success")
        else:
            flash("Помилка оновлення статусу", "error")
    
    return redirect(url_for("admin.orders_management"))

@bp.route("/orders/cancel/<int:order_id>")
@login_required
@admin_required
def cancel_order(order_id):
    with Session() as session:
        order = session.query(Order).filter(Order.id == order_id).first()
        
        if order:
            order.status = OrderStatus.CANCELLED
            session.commit()
            flash("Замовлення скасовано!", "success")
        else:
            flash("Замовлення не знайдено", "error")
    
    return redirect(url_for("admin.orders_management"))