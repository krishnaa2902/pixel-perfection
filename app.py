from flask import Flask, render_template, request, redirect, url_for,session,send_file
import credentials as c
from io import BytesIO
import ibm_db
import base64
from PIL import Image, ImageEnhance,ImageFilter
from custom_effects import *



app = Flask(__name__)
app.secret_key = 'something'

#connection of ibm db2
conn_string = "database="+c.db+";hostname="+c.hostname+";port="+c.port+";uid="+c.uid+";password ="+c.pwd+";security= SSL;sslcertificate = DigiCertGlobalRootCA.crt;"
conn = ibm_db.connect(conn_string,"","")
# print("connection successful")


# Home page
@app.route('/')
def home():
    return render_template('index.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        sql = "select * from USERDEMO where username=? and password=?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt,1,username)
        ibm_db.bind_param(stmt,2,password)
        ibm_db.execute(stmt)    
        user = ibm_db.fetch_assoc(stmt)
        if user: 
            session["username"] = username
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid username or password'
            return render_template('login.html', error=error)
    else:
        return render_template('login.html')

# Registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        #check user in db        
        sql = "SELECT * FROM USERDEMO WHERE email = ? or username = ?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt,1,email)
        ibm_db.bind_param(stmt,2,username)
        ibm_db.execute(stmt)
        stud = ibm_db.fetch_assoc(stmt)
        # print(stud)
        if stud:
            msg = "student details exists . no need to create new user"
            return render_template('register.html', msg=msg)
        else:
            #push user into db
            sql = 'insert into USERDEMO values (?,?,?)'
            stmt = ibm_db.prepare(conn, sql)
            ibm_db.bind_param(stmt,1,username)
            ibm_db.bind_param(stmt,2,password)
            ibm_db.bind_param(stmt,3,email)
            ibm_db.execute(stmt)
            msg="Successfully registered.Please use same credentials to login"
            # return render_template('login.html',msg=msg)
            return redirect(url_for('login',msg=msg))
         
    else:
        return render_template('register.html')

# Dashboard page
@app.route("/dashboard",methods=['GET', 'POST'])
def dashboard():
    # if username and request.method=="POST":
    if 'username' in session:
        username = session['username']
        sql = f"SELECT * FROM ALL_IMAGES WHERE username='{username}' "
        stmt = ibm_db.prepare(conn, sql)
        # ibm_db.bind_param(stmt,1,username)
        # ibm_db.bind_param(stmt,1,'dummy')
        ibm_db.execute(stmt) 
        my_images = []
        my_image_names = []
        dictionary = ibm_db.fetch_assoc(stmt)
        
        while dictionary != False:
            dictionary['DATA'] = base64.b64encode(dictionary['DATA']).decode('utf-8')
            # print(dictionary['NAME'])
            my_images.append(dictionary)
            dictionary = ibm_db.fetch_assoc(stmt)
            
        # print(my_images)
        return render_template("dashboard.html",my_images=my_images,username=username)
    else:
        return redirect("/login")

@app.route('/upload', methods=['GET', 'POST'])
# @login_required
def upload():
    # if request.method == 'POST':
    if 'username' in session:
        file = request.files['file']
        image_data = file.read()
        image_name = file.filename
        # i_id = 56
        username = session['username']
        # Insert the image data into the database
        stmt = ibm_db.prepare(conn, "INSERT INTO ALL_IMAGES (name, data, username) VALUES (?, ?, ?)")
        ibm_db.bind_param(stmt, 1, image_name)
        ibm_db.bind_param(stmt, 2, image_data)
        ibm_db.bind_param(stmt, 3,username)
        ibm_db.execute(stmt)

        # ibm_db.close(conn)

        # return redirect(url_for('editor',id=i_id,username=username))
        # return render_template("dashboard.html",my_images=my_images,username=username)
        return redirect(url_for('dashboard'))
    else:
        return redirect("/login")
    
@app.route('/collaborate',methods=['GET', 'POST'])
def collaborate():
    if 'username' in session:
        username = session['username']
        # print(username)
        colab_name = request.form['colab_name']
        # print(colab_name)
        image_name = request.form['image_name']
        sql = f"SELECT * FROM ALL_IMAGES WHERE (username='{username}' AND name='{image_name}' )"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.execute(stmt) 
        result = ibm_db.fetch_assoc(stmt)
        # print(result)
        sql_1 = f"SELECT * FROM USERDEMO WHERE username='{colab_name}'"
        stmt_1 = ibm_db.prepare(conn, sql_1)
        ibm_db.execute(stmt_1) 
        res = ibm_db.fetch_assoc(stmt_1)
        
        if(res):
            stmt2 = ibm_db.prepare(conn, "INSERT INTO ALL_IMAGES (name, data, username,collaborators) VALUES (?, ?, ?, ?)")
            ibm_db.bind_param(stmt2, 1, result['NAME'])
            ibm_db.bind_param(stmt2, 2, result['DATA'])
            ibm_db.bind_param(stmt2, 3, colab_name)
            ibm_db.bind_param(stmt2, 4, username)
            ibm_db.execute(stmt2)
            # print("shared to " + colab_name)
        # else:
        #     print("no user with username " + colab_name)
        return redirect(url_for('dashboard'))
    else:
        return redirect("/login")

@app.route('/del_img/<int:id>', methods= ['GET','POST'])
def del_img(id):
    if 'username' in session:
        sql = f"DELETE FROM ALL_IMAGES WHERE id='{id}' "       
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.execute(stmt) 
        return redirect(url_for('dashboard'))
    else:
        return redirect("/login")
    
@app.route('/rename_img/<int:id>', methods= ['GET','POST'])
def rename_img(id):
    if 'username' in session:
        new_name = request.form.get('new_name')
        sql = f"UPDATE ALL_IMAGES SET NAME = '{new_name}' WHERE id='{id}' "       
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.execute(stmt) 
        return redirect(url_for('dashboard'))
    else:
        return redirect("/login")

@app.route('/editor/<int:id>', methods=['GET', 'POST'])
def editor(id):
    # image_data = get_image_data(1)
    if 'username' in session:
        sql = f"SELECT * FROM ALL_IMAGES WHERE id='{id}' "
        stmt = ibm_db.prepare(conn, sql)
        # ibm_db.bind_param(stmt,1,id)
        ibm_db.execute(stmt) 
        
        image_class = ibm_db.fetch_assoc(stmt)
        INPUT_FILENAME = image_class['NAME']
        image = image_class['DATA']
        image = Image.open(BytesIO(image))
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        im_raw = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return render_template('editing.html',im_curr=im_raw,im_orig=im_raw,id=id,b=0,c=0,h=0,s=0,sh=0,bl=0,se=0,g=0)
    else:
        return redirect("/login")
    
    
@app.route('/process/<int:id>', methods=['POST'])
def process(id):
    # Get slider values from the AJAX request
    if 'username' in session:
        # print('GOT SLIDER VALS')
        br = int(request.form['brightness'])
        c = int(request.form['contrast'])
        s = int(request.form['saturation'])
        h = int(request.form['hue'])
        sh = int(request.form['sharpness'])
        bl = float(request.form['blur'])
        se = int(request.form['sepia'])
        gr = int(request.form['grayscale'])
        base64_str = request.form.get('image_orig')
        
        # Decode the Base64 string to bytes
        image_bytes = base64.b64decode(base64_str.split(',')[1])

        # Open the image from the bytes using PIL
        image = Image.open(BytesIO(image_bytes))

        im_orig = image
        buffered = BytesIO()
        im_orig.save(buffered, format="PNG")
        im_orig = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Apply image processing based on slider values
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.0+(br/100.0))
        
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.0+(c/100.0))
        
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.0+(s/100.0))
        
        # converter = ImageEnhance.Color(image)
        # image = converter.enhance(1.0+(h/100.0))
        image_hsv = image.convert("HSV")
        image_hsv = image_hsv.point(lambda i: (i + h) % 256 if i + h < 256 else i)
        image_hsv = image_hsv.convert("RGB")

        # Adjust hue using colorsys
        image_rgb = image_hsv.convert("RGB")
        r, g, b = image_rgb.split()
        r = r.point(lambda x: x + h)
        image_hsv = Image.merge('RGB', (r, g, b))
        image = image_hsv

        image = image.filter(ImageFilter.GaussianBlur(bl))

        # Adjust sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(sh)
        
        # Apply sepia
        image = apply_sepia(image,se)

        # Apply grayscale
        if gr>0:
            image = image.convert("L")

        buffered = BytesIO()
        image.save(buffered, format="PNG")
        im_raw = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return render_template('editing.html',im_curr=im_raw,im_orig=im_orig,id=id,b=br,c=c,h=h,s=s,sh=sh,bl=bl,se=se,g=gr)

@app.route('/save_img/<int:id>', methods=['GET', 'POST'])
# @login_required
def save_img(id):
    # if request.method == 'POST':
    if 'username' in session:
        base64_str = request.form.get('image_orig')

    # Decode the Base64 string to byte
        img_data = base64.b64decode(base64_str.split(',')[1])
        # Insert the image data into the database
        stmt = ibm_db.prepare(conn, "UPDATE ALL_IMAGES SET data = ? WHERE id=?")
        ibm_db.bind_param(stmt, 1, img_data)
        ibm_db.bind_param(stmt, 2, id)
        ibm_db.execute(stmt)

        # ibm_db.close(conn)

        return redirect(url_for('export',id=id))
    
@app.route('/export/<int:id>', methods=['GET', 'POST'])
# @login_required
def export(id):
    # if request.method == 'POST':
    if True:
        sql = f"SELECT * FROM ALL_IMAGES WHERE id='{id}' "
        stmt = ibm_db.prepare(conn, sql)
        # ibm_db.bind_param(stmt,1,id)
        ibm_db.execute(stmt) 

        image_class = ibm_db.fetch_assoc(stmt)
        INPUT_FILENAME = image_class['NAME']
        image = image_class['DATA']
        image = Image.open(BytesIO(image))
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        im_raw = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return render_template('export.html',im_url=im_raw,id=id)

@app.route('/download', methods=['POST'])
def download():
    id = request.form['im_id']
    sql = f"SELECT * FROM ALL_IMAGES WHERE id='{id}' "
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.execute(stmt) 

    image_class = ibm_db.fetch_assoc(stmt)
    INPUT_FILENAME = image_class['NAME'].split('.')[0]
    image = image_class['DATA']
    image = Image.open(BytesIO(image))
    format = request.form['format']
    quality = request.form['quality']

    # Convert image format
    if format == 'jpg':
        format = 'jpeg'
        image = image.convert('RGB')
    elif format == 'png':
        image = image.convert('RGBA')

    # Resize image based on quality
    if quality == '1080p':
        width, height = 1920, 1080
    elif quality == '720p':
        width, height = 1280, 720
    elif quality == '480p':
        width, height = 854, 480

    image = image.resize((width, height))

    # Save the processed image to a byte buffer
    buffer = BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)

    # Return the processed image as a Flask response for download
    return send_file(buffer, mimetype=f'image/{format}', as_attachment=True, download_name=f'{INPUT_FILENAME}.{format}')

@app.route('/logout', methods=['GET','POST'])
def logout():
    session.clear() 
    return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(debug=True)
