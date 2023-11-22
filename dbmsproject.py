from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import and_, or_, not_
import random
import os

app = Flask(__name__)
CORS(app)
#app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost:5432/projectdb'
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__='users'
    
    UserID=db.Column(db.Integer,primary_key=True)
    Username=db.Column(db.String(80),unique=True,nullable=False)
    Password=db.Column(db.String(120),unique=False,nullable=False)
    Age=db.Column(db.Integer,unique=False)
    Phone=db.Column(db.String(10),unique=False)
        
    def __repr__(self):
        return f"User('{self.Username}')"
    
    
class Admin(db.Model):
    __tablename__='admins'
    
    AdminID=db.Column(db.Integer,primary_key=True)
    Name=db.Column(db.String(120),unique=False,nullable=False)
    Password=db.Column(db.String(120),unique=False,nullable=False)
    
    def __repr__(self):
        return f"Admin('{self.Name}')"
    
    
class Account(db.Model):
    __tablename__='accounts'
    
    AccountNo=db.Column(db.Integer,primary_key=True)
    Type=db.Column(db.String(20),unique=False,nullable=False)
    Balance=db.Column(db.Integer,unique=False,nullable=False,default=0)
    UID=db.Column(db.Integer,db.ForeignKey('users.UserID'),unique=False,nullable=False)
    
    def __repr__(self):
        return f"Account('{self.AccountNo}')"
    
    
class Transaction(db.Model):
    __tablename__='transactions'
    
    
    
    TransactionID=db.Column(db.Integer,primary_key=True)
    FromAccount=db.Column(db.Integer,db.ForeignKey('accounts.AccountNo'),unique=False,nullable=False)
    ToAccount=db.Column(db.Integer,db.ForeignKey('accounts.AccountNo'),unique=False,nullable=False)
    AdminID=db.Column(db.Integer,db.ForeignKey('admins.AdminID'),unique=False,default=0)
    Type=db.Column(db.String(20),unique=False,nullable=False)
    Amount=db.Column(db.Integer,unique=False,nullable=False)
    Date=db.Column(db.String(30))
    
    def __repr__(self):
        return f"Transaction('{self.TransactionID}')"
    
    
class LoanRequest(db.Model):
    __tablename__='loanrequest'
    
    User=db.Column(db.Integer,db.ForeignKey('users.UserID'),primary_key=True)
    Amount=db.Column(db.Integer,unique=False,nullable=False)
    Duration=db.Column(db.Integer,unique=False,nullable=False)
    Admin=db.Column(db.Integer,db.ForeignKey('admins.AdminID'),unique=False,nullable=False)
    
    def __repr__(self):
        return f"LoanRequest('{self.User}')"
    
    
class Loan(db.Model):
    __tablename__='loans'
    
    LoanID=db.Column(db.Integer,primary_key=True)
    AmountRemaining=db.Column(db.Integer,unique=False,nullable=False)
    FixedAmount=db.Column(db.Integer,unique=False,nullable=False)
    PaymentsRemaining=db.Column(db.Integer,unique=False,nullable=False)
    User=db.Column(db.Integer,db.ForeignKey('users.UserID'),nullable=False,unique=False)
    StartDate=db.Column(db.DateTime,default=datetime.utcnow)
    
    def __repr__(self):
        return f"Loan('{self.LoanID}')"
    
    
from flask import request, jsonify


# User Login route
@app.route('/api/userlogin', methods=['POST'])
def userlogin():
    data = request.get_json()
    user = User.query.filter_by(UserID=data['UserID']).first()
    if user and user.Password == data['Password']:
        return jsonify({'message': 'Login successful', 'UserID': user.UserID})
    return jsonify({'message': 'Invalid username or password'}),401


# Admin Login route
@app.route('/api/adminlogin', methods=['POST'])
def adminlogin():
    data = request.get_json()
    admin = User.query.filter_by(AdminID=data['AdminID']).first()
    if admin and admin.Password == data['Password']:
        return jsonify({'message': 'Login successful', 'AdminID': admin.AdminID})
    return jsonify({'message': 'Invalid username or password'}), 401


#User Details Route
@app.route('/api/userdetails', methods=['GET'])
def userdetails():
    data = request.args.get('UserID')
    udetails = User.query.filter_by(UserID=data).first()
    ser_det= {'UserID':udetails.UserID,'Name':udetails.Username,'Age':udetails.Age,'Phone':udetails.Phone}
    accdetails=Account.query.filter_by(UID=data).all()
    ser_acc = [serialize_account(account) for account in accdetails]
    return jsonify({'Userdetails':ser_det},{'Accounts':ser_acc}),201



#Admin Details Route
@app.route('/api/admindetails', methods=['GET'])
def admindetails():
    data = request.args.get('AdminID')
    admindetails = Admin.query.filter_by(AdminID=data).first()
    ser_det= {'AdminID':admindetails.AdminID,'Name':admindetails.Name}
    return jsonify({'Admindetails':ser_det}),201


#Logout
@app.route('/api/logout',methods=['GET'])
def logout():
    return jsonify({'message':'logged out'}),200


#Transaction History Route
@app.route('/api/transactions',methods=['GET'])
def transactions():
    data=request.args.get('AccountNo')
    from_trans=Transaction.query.filter_by(FromAccount=data).all()
    to_trans=Transaction.query.filter_by(ToAccount=data).all()
    ser_trans_from=[serialize_transaction(transaction) for transaction in from_trans]
    ser_trans_to=[serialize_transaction(transaction) for transaction in to_trans]
    ser_trans_from.extend(ser_trans_to)
    
    ser_trans_from.sort(key=sortfunc)
    if(from_trans or to_trans):
        return jsonify({'Transactions':ser_trans_from})
    return jsonify({'message':'Cant find entries'}),404




#User Transaction Payment Route
@app.route('/api/userpayment',methods=['POST'])
def userpayment():
        data = request.get_json()
        fromacc=Account.query.filter_by(AccountNo=data['FromAccount']).first()
        toacc=Account.query.filter_by(AccountNo=data['Toaccount']).first()
        
        if fromacc==None or toacc==None:
            return jsonify({'message':'Invalid Account Number'}),404
        
        amount=data['Amount']
        balance=fromacc.Balance
    
        if amount>balance:
            return jsonify({'message':'Insufficient Balance'}),404
        
        tid=random.randint(100000,900000)
        
        flag=Account.query.filter_by(AccountNo=tid).first()
        
        while(flag):
            tid=random.randint(100000,900000)
            flag=Account.query.filter_by(AccountNo=tid).first()
            
        
        now=str(datetime.now().replace(second=0,microsecond=0))
        print(now)
        trans=Transaction(
                                TransactionID=tid,
                                FromAccount=data['FromAccount'],
                                Toaccount=data['ToAccount'],
                                AdminID=0,
                                Type=data['Type'],
                                Amount=data['Amount'],
                                Date=now
                         )
        
        db.session.add(trans)
        db.session.commit()
        
        fromacc.Balance=fromacc.Balance-amount
        db.session.commit()
        toacc.Balance=toacc.Balance+amount
        db.session.commit()
        
        return jsonify({'message':'Transaction Complete'}),200


#Admin Transaction Payment Route
@app.route('/api/adminpayment',methods=['POST'])
def adminpayment():
        data = request.get_json()
        fromacc=Account.query.filter_by(AccountNo=data['FromAccount']).first()
        toacc=Account.query.filter_by(AccountNo=data['Toaccount']).first()
        
        if fromacc==None or toacc==None:
            return jsonify({'message':'Invalid Account Number'}),404
        
        amount=data['Amount']
        admin=data['AdminID']
        balance=fromacc.Balance
        
    
        if amount>balance:
            return jsonify({'message':'Insufficient Balance'}),404
        
        tid=random.randint(100000,900000)
        
        flag=Account.query.filter_by(AccountNo=tid).first()
        
        while(flag):
            tid=random.randint(100000,900000)
            flag=Account.query.filter_by(AccountNo=tid).first()
            
        
        now=str(datetime.now().replace(second=0,microsecond=0))
        print(now)
        trans=Transaction(
                                TransactionID=tid,
                                FromAccount=data['FromAccount'],
                                Toaccount=data['ToAccount'],
                                AdminID=admin,
                                Type=data['Type'],
                                Amount=data['Amount'],
                                Date=now
                         )
        
        db.session.add(trans)
        db.session.commit()
        
        fromacc.Balance=fromacc.Balance-amount
        db.session.commit()
        toacc.Balance=toacc.Balance+amount
        db.session.commit()
        
        return jsonify({'message':'Transaction Complete'}),200


#Check User Details Route
@app.route('/api/checkuser',methods=['GET'])
def checkuser():  
    data=request.args.get('UserID')
    useracc= User.query.filter_by(UserID=data).first()
    
    if not useracc:
        return jsonify({'message':'User Not Found'}),404
    
    ser_det= {'UserID':useracc.UserID,'Name':useracc.Username,'Age':useracc.Age,'Phone':useracc.Phone}
    accdetails=Account.query.filter_by(UID=data).all()
    ser_acc = [serialize_account(account) for account in accdetails]
    return jsonify({'Userdetails':ser_det}),201


#Create User Route 
@app.route('/api/createuser',methods=['POST'])
def createuser():
        data = request.get_json()
        
        uid=random.randint(100000,900000)
        
        flag=User.query.filter_by(UserID=uid).first()
        
        while(flag):
            uid=random.randint(100000,900000)
            flag=User.query.filter_by(UserID=uid).first()
            
        
        
        newuser=User(
                                UserID=uid,
                                Username=data['Username'],
                                Password=data['Password'],
                                Age=data['Age'],
                                Phone=data['Phone']
                         )
        
        db.session.add(newuser)
        db.session.commit()

        return jsonify({'message':'User Created Successfully'}),200
    
    
#Delete User Route
@app.route('/api/deleteuser',methods=['POST'])
def deleteuser():
        data = request.get_json()
        
        uid=User.query.filter_by(UserID=data['UserID']).first()
        
        if not uid:
            return jsonify({'message':'User Not Found'}),401
        
        loans=Loan.query.filter_by(User=data['UserID']).all()
        
        if loans:
            return jsonify({'message':'User has unclosed Loans.Failed to delete user'}),401

        accdetails=Account.query.filter_by(UID=data['UserID']).all()
        for account in accdetails:
            db.session.delete(account)
            db.session.commit()
            
        db.session.delete(uid)
        db.session.commit()
        
        return jsonify({'message':'User and their accounts deleted successfully'}),200
            
            

        
        
        
        
        

    
    
        



def serialize_account(account):
    return {
                'AccountNo':account.AccountNo,
                'Type':account.Type,
                'Balance':account.Balance       
            }
    
    
def serialize_transaction(trans):
    return {
                'TransactionID':trans.TransactionID,
                'FromAccount':trans.FromAccount,
                'ToAccount':trans.ToAccount,
                'Type':trans.Type,
                'Amount':trans.Amount,
                'Date':trans.Date,
    }
    
def sortfunc(x):
    return{
           x['Date']
    }

    

    
    


@app.route('/')
def index():
    return "<h1 style='color : red'>hello world</h1>"

def initialize_database():
    with app.app_context():
        try:
            db.create_all()
            def_admin = Admin(AdminID='007', Name='Master', Password='password')
            db.session.add(def_admin)
            db.session.commit()
            print("Database initialized.")
        except Exception as e:
            print(f"An error occurred while initializing the database: {e}")
            
   


if __name__=="__main__":
    initialize_database()
    app.run()
    