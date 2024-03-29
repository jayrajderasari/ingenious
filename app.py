from flask import Flask, render_template, request, redirect, url_for, send_file
import google.generativeai as genai
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from PIL import Image
import json
import base64
app = Flask(__name__)
users = {
    'vrunda': '123',
    'jayraj': '456' 
}
data = {'vrunda': [],
        'jayraj': []}


activeUser = ""

def dataMaker(activeUser, img):
    global data
    print('datamaker',activeUser)
    genai.configure(api_key='AIzaSyBLb-imm7q-1VwWYo6Ia03ap13py0L5mSU')
    model = genai.GenerativeModel('gemini-pro-vision')
    
    response = model.generate_content(["You need to fetch the data from this image. Respond back in JSON string format without triple quotes and json keyword. These should be the keys of the data in JSON [invoice_no, name of seller, cgst_amount, sgst_amount, bill_amount, date, category of expense from:(Personal, Entertainment, Medical, Household, Leisure, Education, Others); write NA for data not available]", img])
    d = json.loads(response.text)
    data[activeUser].append(d)
    print(response.text)
    return True

def dataDisplay(activeUser):
    global data
    if data[activeUser]:
        return data[activeUser]
    else:
        return []

def generate_pdf_file(user_data):
    doc = SimpleDocTemplate("table.pdf", pagesize=letter)
    elements = []
    table_data = []
    temp = ['Invoice_Id','Seller','CGST','SGST','Amount','Date','Category']
    table_data.append(temp)    

    for i in user_data:
        temp = [float(value) if value.replace('.', '', 1).isdigit() else value for value in i.values()]
        table_data.append(temp)    

    table = Table(table_data)
    style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.white),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)])
    table.setStyle(style)
    elements.append(table)
    doc.build(elements)
    return "table.pdf"

@app.route('/', methods=['GET', 'POST'])
def index():
    global activeUser
    dataURI = []
    if activeUser == '':
        return render_template('login.html')
    if request.method == 'POST':
        dataURI = []
        print('post',activeUser)
        if 'img' in request.files:
            img_file = request.files.getlist('img')
            for i in img_file:
                img_bytes = i.read()
                img = Image.open(BytesIO(img_bytes))

                encoded_string = base64.b64encode(img_bytes).decode("utf-8")
                dataURI.append(encoded_string)
                dataMaker(activeUser, img)
        else:    
            pdf_file = generate_pdf_file(data[activeUser])
            return send_file(pdf_file, as_attachment=True, download_name='report.pdf')            
    data_display = dataDisplay(activeUser)  # Assign result to a different variable
    totalExp = 0
    cgstSum = 0
    sgstSum = 0
    for d in data_display:
        totalExp += float(d['bill_amount'].replace('NA','0'))
        cgstSum += float(d['cgst_amount'].replace('NA','0'))
        sgstSum += float(d['sgst_amount'].replace('NA','0'))
    return render_template('index.html',data_display=data_display,activeUser=activeUser,totalExp=totalExp,cgstSum=cgstSum,sgstSum=sgstSum,dataURI=dataURI)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    global activeUser
    if username in users and users[username] == password:
        activeUser = username
        return redirect(url_for('index'))
    else:
        return render_template('login.html', message='Invalid username or password')

@app.route("/login")
def login_page():
    return render_template("login.html")

if __name__ == "__main__":
    app.run(debug=True)