from flask import Flask,render_template,redirect,request,url_for,flash,session
from datetime import datetime,timedelta
from applications.models import Parkinglot, Parkingspot, Reservepkspot
from flask import current_app as app 
from sqlalchemy.orm import joinedload
import math

from .models import * 

@app.route("/login", methods=["GET","POST"]) 
def login():
    if request.method == "POST":
        email = request.form.get("email")
        pwd= request.form.get("password")
        this_user = User.query.filter_by(email=email).first()
        if this_user:
            if this_user.password == pwd:
                session["user_id"] = this_user.id
                if this_user.type == "admin": 
                    return redirect(url_for('admin_dash'))
                else:
                    return redirect(url_for('user_dash'))
            else:
                flash("password is incorrect")
                return redirect(url_for('login'))
        else:
            flash("User does not exist")
            return redirect(url_for('login'))      
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        pwd = request.form.get("password")
        name = request.form.get("fullname")
        pincode = request.form.get("pincode")
        address = request.form.get("address")

        this_user = User.query.filter_by(email=email).first()
        if this_user:
            flash("user already exists")
        else:
            is_first_user = User.query.count() == 0
            user_type = "admin" if is_first_user else "general"

            new_user = User(email=email,password=pwd,name=name,pincode=pincode,address=address,type=user_type)
            db.session.add(new_user)
            db.session.commit()
            return redirect("/login")
    return render_template("signup.html")


@app.route("/add_lot", methods=["GET","POST"])
def add_lot():
    if request.method == "POST":
        prime_location = request.form['prime-location-name']
        address = request.form['address']
        try:
            pincode = int(request.form['pincode'])
            price = int(request.form['price'])
            max_spots = int(request.form['max-spots'])
        except ValueError:
            flash("Pincode, Price, and Maximum Spots must be numbers.", "danger")
            return redirect(url_for('add_lot'))
        new_lot = Parkinglot(prime_location_name=prime_location,address=address,pincode=int(pincode),price=int(price),max_no_of_spots=max_spots)
        db.session.add(new_lot)
        db.session.commit()
        for _ in range(max_spots):
            new_spot = Parkingspot(lot_id=new_lot.id, status='A')
            db.session.add(new_spot)

        db.session.commit()
        return redirect(url_for('admin_dash'))
    return render_template('add_lot.html')

@app.route("/admin")
def admin_dash():
    search_value = request.args.get("search_value")
    
    if search_value:
        if search_value.isdigit():
            lots = Parkinglot.query.options(joinedload(Parkinglot.spots)).filter(
                Parkinglot.pincode == int(search_value)
            ).all()
        else:
            lots = Parkinglot.query.options(joinedload(Parkinglot.spots)).filter(
                Parkinglot.prime_location_name.ilike(f"%{search_value}%")
            ).all()
    else:
        lots = Parkinglot.query.options(joinedload(Parkinglot.spots)).all()

    for lot in lots:
        total_count = len(lot.spots)
        available_count = sum(1 for spot in lot.spots if spot.status == 'A')
        occupied_count = sum(1 for spot in lot.spots if spot.status == 'O')

        setattr(lot, 'total_spots', total_count)
        setattr(lot, 'available_spots', available_count)
        setattr(lot, 'occupied_count', occupied_count)
    return render_template('admin_dash.html', lots=lots, search_value=search_value)
   
@app.route('/edit_lot/<int:lot_id>', methods=['GET', 'POST'])
def edit_lot(lot_id):
    lot = Parkinglot.query.get_or_404(lot_id)

    if request.method == 'POST':
        try:
            new_max_spots = int(request.form['max-spots'])
        except ValueError:
            flash("Invalid number for max spots.", "danger")
            return redirect(url_for('edit_lot', lot_id=lot_id))

        occupied_count = Parkingspot.query.filter_by(lot_id=lot.id, status='O').count()

        if new_max_spots < occupied_count:
            flash(f"Cannot reduce max spots below occupied count ({occupied_count}).", "warning")
            return redirect(url_for('edit_lot', lot_id=lot_id))
        
        current_spots = Parkingspot.query.filter_by(lot_id=lot.id).all()
        current_total = len(current_spots)

        if new_max_spots > current_total:
            for _ in range(new_max_spots - current_total):
                new_spot = Parkingspot(lot_id=lot.id, status='A')
                db.session.add(new_spot)

        elif new_max_spots < current_total:
            to_remove = current_total - new_max_spots
            available_spots = [spot for spot in current_spots if spot.status == 'A']

            if len(available_spots) < to_remove:
                flash("Not enough available spots to remove. Try reducing less.", "warning")
                return redirect(url_for('edit_lot', lot_id=lot_id))
            
            for spot in available_spots[:to_remove]:
                db.session.delete(spot)

        lot.max_no_of_spots = new_max_spots
        db.session.commit()
        flash("Parking lot updated successfully.", "success")
        return redirect(url_for('admin_dash'))
    occupied_count = Parkingspot.query.filter_by(lot_id=lot.id, status='O').count()
    return render_template('edit_lot.html', lot=lot, occupied_count=occupied_count)

@app.route('/delete_lot/<int:lot_id>', methods=['POST'])
def delete_lot(lot_id):
    lot = Parkinglot.query.get_or_404(lot_id)

    has_occupied = any(spot.status == 'O' for spot in lot.spots)
    if has_occupied:
        flash("Cannot delete lot with occupied spots.", "warning")
        return redirect(url_for('admin_dash'))
    db.session.delete(lot)
    db.session.commit()
    flash("Parking lot deleted successfully.", "success")
    return redirect(url_for('admin_dash'))

@app.route('/delete_spot/<int:spot_id>', methods=['POST'])
def delete_spot(spot_id):
    spot = Parkingspot.query.get_or_404(spot_id)

    if spot.status == 'O':
        flash("Cannot delete an occupied spot.", "warning")
        return redirect(url_for('admin_dash'))
    
    lot = spot.lot

    db.session.delete(spot)
    if lot.max_no_of_spots > 0:
        lot.max_no_of_spots -= 1
    db.session.commit()
    flash("Spot deleted successfully.", "success")
    return redirect(url_for('admin_dash'))


@app.route("/users")
def users():
    search_query = request.args.get("query", "").strip()

    if search_query:
        if search_query.isdigit():
            all_users = User.query.filter(User.id == int(search_query)).all()
        else:
            all_users = User.query.filter(User.email.ilike(f"%{search_query}%")).all()
    else:
        all_users = User.query.all()[1:] 

    return render_template('users.html', users=all_users, search_query=search_query)


@app.route('/user_dash')
def user_dash():
    user_id = session.get("user_id")
    reservations = Reservepkspot.query.filter_by(user_id=user_id).all()
    search_location = request.args.get("query", "")
    user = User.query.get(user_id)

    if search_location:
        lots = Parkinglot.query.options(joinedload(Parkinglot.spots)).filter(
            db.or_(
                Parkinglot.prime_location_name.ilike(f"%{search_location}%"),
                Parkinglot.pincode.ilike(f"%{search_location}")
            )
        ).all()
    else:
        lots = Parkinglot.query.options(joinedload(Parkinglot.spots)).all()

    for lot in lots:
        available_count = sum(1 for spot in lot.spots if spot.status == 'A')
        setattr(lot, 'available_spots', available_count)

    return render_template("user_dash.html",reservations=reservations,lots=lots,search_location=search_location,email=session.get("email"), user=user)

@app.route('/book_spot/<int:lot_id>', methods=["GET", "POST"])
def book_spot(lot_id):
    user_id = session.get("user_id")
    lot = Parkinglot.query.get_or_404(lot_id)

    if request.method == "POST":
        spot_id = request.form.get("spot_id")
        vehicle_no = request.form.get("vehicle_no")
        spot = Parkingspot.query.get_or_404(spot_id)

        if spot.status != 'A':
            flash("Spot is not available", "danger")
            return redirect(url_for("user_dash"))

        spot.status = 'O'
        reservation = Reservepkspot(spot_id=spot.id,user_id=user_id,vehicle_no=vehicle_no,parking_timestamp=datetime.utcnow(),leaving_timestamp=None,cost_per_time=lot.price)
        db.session.add(reservation)
        db.session.commit()
        return redirect(url_for("user_dash"))
    else:
        available_spot = next((s for s in lot.spots if s.status == 'A'), None)
        if not available_spot:
            flash("No available spots", "warning")
            return redirect(url_for("user_dash"))
        return render_template("book_spot.html", spot=available_spot, lot=lot, user={"id": user_id})

@app.route('/release_spot/<int:reservation_id>', methods=['GET', 'POST'])
def release_spot(reservation_id):
    reservation = Reservepkspot.query.get_or_404(reservation_id)
    spot = reservation.spot
    lot = spot.lot

    if request.method == 'POST':
        if spot.status != 'O':
            return redirect(url_for("user_dash"))

        reservation.leaving_timestamp = datetime.utcnow()
        spot.status = 'A'
        duration = reservation.leaving_timestamp - reservation.parking_timestamp
        hours = duration.total_seconds() / 3600
        rounded_hours = math.ceil(hours)
        cost = round(rounded_hours * lot.price, 2)
        reservation.parking_cost = cost 
        db.session.commit()
        flash("Spot released successfully.", "success")
        return redirect(url_for("parking_history"))
    now = datetime.utcnow()
    duration = now - reservation.parking_timestamp
    hours = duration.total_seconds() / 3600
    rounded_hours = math.ceil(hours)
    cost = round(rounded_hours * lot.price, 2)
    return render_template("release_spot.html", reservation=reservation, now=now, cost=cost)

@app.route("/parking_history")
def parking_history():
    user_id= session.get("user_id")
    if not user_id:
        flash("Please log in to view your parking history", "error")
        return redirect("/login") 
    reservations = Reservepkspot.query.filter_by(user_id=user_id).all()
    for r in reservations:
        if r.leaving_timestamp is None:
            duration = datetime.utcnow() - r.parking_timestamp
            hours = duration.total_seconds() / 3600
            rounded_hours = math.ceil(hours)
            r.parking_cost = round(rounded_hours * r.spot.lot.price, 2)
    return render_template("parking_history.html", reservations=reservations,timedelta=timedelta)


@app.route("/view_spot/<int:spot_id>",methods=["GET"])
def view_spot(spot_id):
    spot = Parkingspot.query.get_or_404(spot_id)
    return render_template("view_spot.html", spot=spot)

@app.route("/view_occupied_spot/<int:spot_id>")
def view_occupied_spot(spot_id):
    
    spot = Parkingspot.query.get_or_404(spot_id)
    reservation = Reservepkspot.query.filter_by(spot_id=spot_id).order_by(Reservepkspot.parking_timestamp.desc()).first()
    
    if not reservation:
        flash("No reservation found for this spot.")
        return redirect(url_for("admin_dash"))

    return render_template("occupied_spot.html", spot=spot, reservation=reservation)

@app.route('/edit_user_profile',methods=['GET','POST'])
def edit_user_profile():
    user_id = session.get("user_id")  
    if not user_id:
        return redirect("/login") 

    user = User.query.get(user_id) 
    if request.method=='POST':
        user.email=request.form['email']
        user.pincode=request.form['pincode']
        user.name=request.form['fullname']
        user.password = request.form['password']  
        user.address = request.form['address']
        db.session.commit()
        return redirect(url_for('user_dash'))
    return render_template("edit_user_profile.html", user=user)

@app.route('/edit_admin_profile',methods=['GET','POST'])
def edit_admin_profile():
    user_id = session.get("user_id") 
    if not user_id:
        return redirect("/login") 

    user = User.query.get(user_id) 
    if request.method=='POST':
        user.email=request.form['email']
        user.pincode=request.form['pincode']
        user.name=request.form['fullname']
        user.password = request.form['password']
        user.address = request.form['address']
        db.session.commit()
        return redirect(url_for('admin_dash'))
    return render_template("edit_admin_profile.html", user=user)


@app.route("/user_summary")
def user_summary():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    reservations = Reservepkspot.query.filter_by(user_id=user_id).order_by(Reservepkspot.parking_timestamp.desc()).limit(10).all()

    data = {
        "dates": [r.parking_timestamp.strftime("%Y-%m-%d") for r in reservations],
        "costs": [r.cost_per_time for r in reservations],
    }

    return render_template("user_summary.html", data=data)

@app.route("/admin_summary")
def admin_summary():
    available = Parkingspot.query.filter_by(status='A').count()
    occupied = Parkingspot.query.filter_by(status='O').count()

    data = {
        "labels": ["Available", "Occupied"],
        "counts": [available, occupied]
    }

    return render_template("admin_summary.html", data=data)

