from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from cs50 import SQL
from tempfile import mkdtemp
from PIL import Image 
from pathlib import Path
from twilio.rest import Client
from bidi.algorithm import get_display
import arabic_reshaper

app = Flask(__name__)



#the backend is not yet routed to the frontend

# making the session 
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.debug = True
Session(app)

# selecting the data base
db = SQL("sqlite:///lawyers.db")


@app.route("/")
def index():

    lawyers = db.execute("SELECT name,total_rating ,city FROM lawyers ORDER BY total_rating DESC LIMIT 10 ")
    result = db.execute("SELECT subject,description,law_id FROM iraqi_law ")
    return render_template("home.html",len= len(result), result=result , head="القانون العراقي", link="laws" , lawyer =lawyers)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    allowed=['png', 'jpg', 'jpeg']
    citys=["كركوك", "بابل","بغداد","بصرة"]

    if request.method == "POST" :
        # saving the received data in variables for easier use
        city = request.form.get("city")
        name = request.form.get("name")
        password = request.form.get("password")
        email = request.form.get("email")
        number = request.form.get("number")
        licens = request.files['license']
        pic = request.files['pic']

        pic_extention = pic.filename.split(".")[-1].lower()
        licens_extention = licens.filename.split(".")[-1].lower()

        #checking file type
        if pic_extention not in allowed or licens_extention not in allowed :
            error="صيغة الصورة غير مقبولة"


        # if the email is already taken display an error page
        elif len(db.execute("SELECT email FROM lawyers WHERE email = ?", email)) != 0:
            error= "البريد الاكتروني مستخدب بالفعل"

        # checking for valid input from the city selector
        elif city not in citys:
            error = "المحافظة غير موجودة"

        #insert the new lawyer
        else:
            #making international number
            if number[0] == "0":
                number = number.replace("0","+964", 1) 
        
            db.execute("INSERT INTO lawyers ('name', 'password', 'email', 'number', 'verfied', 'city' ,'total_rating') VALUES (? , ?, ?, ?, 1 , ?, 0)", name, generate_password_hash(password), email, number ,city)
            user_id = db.execute("SELECT id FROM lawyers WHERE email = ?", email)[0]["id"]
                
            # making image path and naming the image by thier user id
            lice_path = Path("C:/Users/hassa/Videos/lawyers1/static/doc/lic/{}.{}".format(user_id, licens_extention))
            pic_path = Path("C:/Users/hassa/Videos/lawyers1/static/doc/pic/{}.{}".format(user_id, pic_extention))
            
            pic_path1="/static/doc/pic/{}.{}".format(user_id, pic_extention)
            lice_path1="/static/doc/lic/{}.{}".format(user_id, licens_extention)
            #saving the image path
            db.execute("UPDATE lawyers SET license = ?, picture = ? WHERE id = ? ", str(lice_path1), str(pic_path1), user_id) 

            #saving the a images to their file path
            licens.save(lice_path)
            pic.save(pic_path)
        
            return redirect("/")

        return render_template("login.html",error=error)

    else:
        return render_template("login.html")




@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST" :

        person = db.execute("SELECT * FROM lawyers WHERE email = ?" , request.form.get('email') )
        password = request.form.get('password')

        #if the email is not in the database
        if len(person) !=  1:
            error = "البريد الالكتروني غير صحيح"

        #if the password is not correct
        elif not check_password_hash ( person[0]["password"], password) :
            error = "الرمز السري غير صحيح"
            
        #save the session id
        else:
            session["user_id"] = person[0]["id"]
            return redirect("/")

        return render_template("login.html",error = error)

    else:
        return render_template("login.html",error = error)


@app.route("/profile-edit")
def profile():

    # if the person has not yet sign/log in redirect him
    if session.get("user_id") is None:
        return redirect("/login")

    else:
        n = db.execute("SELECT * FROM lawyers WHERE id = ?", session["user_id"])
        return render_template("profile.html" , name=n[0]["name"] , email=n[0]["email"] , number=n[0]["number"], location=n[0]["address"])
 
@app.route("/profile/<id>")  
def landing_page(id):

        n = db.execute("SELECT * FROM lawyers WHERE id = ?", id)
        return render_template("profile.html" , name=n[0]["name"] , email=n[0]["email"] , number=n[0]["number"], location=n[0]["address"])



@app.route("/logout", methods=["GET", "POST"])
def logout():
    if request.method == "POST" :
    #delete the session id
        session.clear()
        return redirect("/")

@app.route("/requst/<id>", methods=["GET", "POST"])
def requst(id):
    if request.method== "POST" :
        
        number = request.form.get("number")


        lawyer = db.execute("SELECT name, number FROM lawyers WHERE id = ?", id)
        name = request.form.get("name")
        descrip = request.form.get("descrip")
        lawyer_number = lawyer[0]["number"]

        # send the requst to the lawyer phone number"
        
        s1 = " تلقيت طلب من موقع محاميكم . "
        s2= " اسم الزبون "
        s3 = " رقم هاتفه "
        s4 = " مشكلته : "
        requst=arabic_reshaper.reshape(s1 + s2 + name + s4 + descrip  + s3 + number)
        account_sid = 'AC0394b39ffb198e04993c2c61415e5d62' 
        auth_token = '1ea55549f5573f714465edf2f31c46f6' 
        client = Client(account_sid, auth_token) 
        message = client.messages.create (from_="whatsapp:+14155238886", body=requst, to= "whatsapp:" + lawyer_number) 

        result =  db.execute("SELECT client_num FROM requset WHERE client_num = ? AND lawyer_id = ? ", number, id)

        if len(result) == 0 :
            db.execute("INSERT INTO requset ('lawyer_id', 'client_num') VALUES (?, ?)", id, number)
    
        return redirect("/")
    else:
        return render_template("requst.html",id = id )
        

@app.route("/lawyers-search", methods=["GET", "POST"])
def search():

    if request.method == "POST" :
        name = f"%{request.form.get('Search')}%"
        city= request.form.get('city')
        rating_list=[]
        if city == "all":
            result = db.execute("SELECT name, picture, total_rating, city FROM lawyers WHERE name LIKE ? AND verfied = 1  ", name)
     
        else :
            result = db.execute("SELECT name, picture, total_rating ,city FROM lawyers WHERE name LIKE ? AND city = ? AND verfied = 1  ", name, city)          
        

        return render_template ("lawy-result.html",lawyer= result , len= len(result) ,rating= rating_list)


    else:
        result = db.execute("SELECT name, picture,total_rating,city FROM lawyers WHERE verfied = 1 ")
        return render_template("lawy-result.html",lawyer= result , len= len(result))



@app.route("/law/<id>" ,methods=["GET", "POST"])
def law(id):    
    if request.method == "POST" :

        search = request.form.get('Search')
        text = []   
        result= []
        for i in range(1,11):
            law = Path (db.execute("SELECT law FROM iraqi_law WHERE law_id = ?", id )[0]["law"] + f"/{i}.txt")
            with open ( law , encoding='utf-8') as f:
                text.append ( { "description" : f.read() , "subject" :f" { i } المادة " } )
        for i in range(0,10):       
            if search in text[i]["description"]:
                text[i]["description"]=arabic_reshaper.reshape(text[i]["description"])
                result.append(text[i]) 
        return render_template("law-search.html" , len=len(result) , result= result ,head = search, link = f"/law/{id}" )
                   
    else:
        
        head = db.execute("SELECT subject FROM iraqi_law WHERE law_id = ?", id )[0]["subject"]
        text = []   
        for i in range(1,11):
            law = Path (db.execute("SELECT law FROM iraqi_law WHERE law_id = ?", id )[0]["law"] + f"/{i}.txt")
            with open ( law , encoding='utf-8') as f:
                text.append ( { "description" : arabic_reshaper.reshape(f.read()) , "subject" :f" { i } المادة " } )
        return render_template("law-search.html", len=len(text), result= text, head=head, link=f"/law/{id}" )



@app.route("/laws", methods=["GET", "POST"])
def laws():    
    if request.method == "POST" :
        law = f"%{request.form.get('Search')}%"
        result = db.execute("SELECT subject,description,law_id FROM iraqi_law WHERE subject LIKE ?", law )
        return render_template("law-search.html", len= len(result), result=result , head="القانون العراقي", link="laws", placeholder= "اسم القانون" )
    else:
        result = db.execute("SELECT subject,description,law_id FROM iraqi_law ")
        return render_template("law-search.html", len= len(result), result=result , head="القانون العراقي", link="laws", placeholder= "اسم القانون")


@app.route("/review/<id>", methods=["GET", "POST"])
def review(id):    
    if request.method == "POST" :
        number = request.form.get('number')
        result1 = db.execute("SELECT client_num FROM requset WHERE client_num = ? AND lawyer_id = ? ", number, id)
        result2 = db.execute("SELECT reviewer_num FROM review WHERE reviewer_num = ? AND lawyer_id = ? ", number, id)

        if len(result1) == 1 and len(result2) == 0:
            review = request.form.get('rate')
            details = request.form.get('descrip')
            db.execute("INSERT INTO review (reviewer_num, lawyer_id, review, details) VALUES ( ?, ?, ?, ?)", number, id, review, details )
            
            ratings=db.execute("SELECT review FROM review WHERE lawyer_id = ?" ,id)
            rating_sum = 0
            for i in range(len(ratings)):
                rating_sum += ratings[i]["review"]
            total = rating_sum / len(ratings)
            db.execute("UPDATE lawyers SET total_rating = ? WHERE id = ?", total, id)

            return redirect("/")

        elif len(result2) != 0:
            return render_template("review.html", id =id)
            # do want modify

        elif  len(result1) != 1:
            return render_template("review.html", id =id)
            # you need to send message first
    else:
        return render_template("review.html", id =id)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST" :
        pass
    else:
        unregister=db.execute("SELECT name , number , picture , license FROM lawyers WHERE verfied = 0")
        render_template("admin.html", unreg = unregister)


#lawyer page repeat
#adman shit

#laws txt
#editing  page
#admin page
# انتهاء صلاحية الاهوية
#register in nav bar
#cheack messaging for other numbers


# find and len of the word so we highlight it
# make email requset


