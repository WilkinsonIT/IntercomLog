from flask import *
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from datetime import *
import sys
import sched
import time as t
import threading
#MCSIntercomLog

from datetime import date
app = Flask(__name__)
SnomStatus = {}
email_sender_account = "mcsintercomlog@gmail.com"
email_sender_username = "mcsintercomlog@gmail.com"
email_sender_password = "Morgank12"
email_smtp_server = "smtp.gmail.com"
email_smtp_port = 587
email_recipients = "wtwilkinson@morgank12.org"
email_subject = "SNOM WARNING"




#Make sure we are only reporting between hours, Snoms will not receive calls at night obviously
def BetweenHours(currentTime):
    start = time(8,0,0)
    end = time(15,0,0)
    if (start <= currentTime.time() and currentTime.time() <= end):
        return True
    else:
        return False

def SendMail(device,reason):
            server = smtplib.SMTP(email_smtp_server,email_smtp_port)
            server.starttls()
            server.login(email_sender_username,email_sender_password)
            
            #for recipient in email_recipients:
            print(f"Sending email")  
            message = MIMEMultipart('alternative')
            message['From'] = email_sender_account
            message['To'] = email_recipients
            message['Subject'] = email_subject

            email_body = """<html>
<head>
  <title>Warning from SNOM {device}</title>
</head>

<body>
  <h1>Snom {device} has reported a warning status</h1>
  <p>Automated alert from SnomLogger</p>
</body>

</html>""".format(device=device)              
        
                        
            message.attach(MIMEText(email_body, 'html'))
            text = message.as_string()
            server.sendmail(email_sender_account,email_recipients,text)
            server.quit()
        

def CheckUp():
    #This thread will check every hour to see if a Snom has been inactive (Should atleast get a bell every hour)
    currentTime = datetime.now() 
    global fname
    print("Local time:" , currentTime, "| Checking Status")
    fname = currentTime.strftime("%m_%d_%y")
    fname = fname + "_LogEvents.txt"
    print(fname)  
    
    for key in SnomStatus:      
        delta = currentTime - SnomStatus[key]
        delta.total_seconds()
        print(delta.total_seconds())
        if(delta.total_seconds() > 7200 and BetweenHours(currentTime)):
            f = open(fname, "a+")
            f.write("[X]SNOM DOWN " + key + " Did not report in two hours!\n")
            print("[X]SNOM DOWN " + key + " Did not report in two hours!")
            f.close()
            SendMail(key,"Did not report")
        
        elif(BetweenHours == False):
            print("Not between hours waiting...")
            

        else:
            print("Status: OK 200")
            
    t.sleep(3600)
    CheckUp()

    return True

def LogHandler(ActiveCalls,CallID,Reason):
        #If we have more than one active call this could indicate an issue or busy line
        print("Reason: ", Reason)
        if(Reason == "Missed Call"):
            print("[X] Snom " + request.remote_addr + " Missed a call!")
            f = open(fname,"a+")
            f.write("[X] Snom " + request.remote_addr + " Missed a call!\n")
            SendMail(request.remote_addr,"Missed Call")
            f.close()
        elif(Reason=="Hold"):
            print("[X] Snom " + request.remote_addr + " Missed a call: Hold!\n")
            f = open(fname,"a+")
            f.write("[X] Snom " + request.remote_addr + "Missed a call: Hold!\n")
            SendMail(request.remote_addr,"On Hold")
            f.close()
        elif(Reason =="OnHook"):
            print("[X] Snom " + request.remote_addr + "Missed a call: OnHook\n")        
            f = open(fname,"a+")
            f.write("[X] Snom " + request.remote_addr + "Missed a call: OnHook\n")
            f.close()
            SendMail(request.remote_addr,"On Hook")
        elif(Reason =="DND"):
            print("[X] Snom " + request.remote_addr + "Missed a call: DND On\n")
            f = open(fname,"a+")
            f.write("[X] Snom " + request.remote_addr + "Missed a call: DND On\n")
            SendMail(request.remote_addr,"DND mode")
            f.close()

        print("Active Calls: ",ActiveCalls)
        if(int(ActiveCalls) > 1):
            print("[X]Detected more than 1 active call collission?")
            f = open(fname,"a+")
            f.write("[X]Possible Collission on call " + request.remote_addr + "\n")
            f.close()

        #Resolve IP to host and timestamp calls
        print("Call ID:", CallID)
        f = open(fname, "a+")
        schoolname = ""
        ctime = datetime.now()
        current_timestr = t.strftime("%H:%M:%S")
        

        f.write(current_timestr + ": " + "Snom " + request.remote_addr + " " + "Called" + "\n")
        f.close()

        #Add the school and time of call to our dictionary to reference time between each call
        SnomStatus[request.remote_addr] = ctime
        
        print(ctime,":","Snom",request.remote_addr,"Event",str(Reason).capitalize())
        #print("Status for All Snoms Updated:")
        #for pair in SnomStatus.items():
        #    print(pair)
        return "Success"
       

@app.route('/LogInvite',methods=['GET','POST'])
def LogSnom():
    #print('Snom called')
    #Process Get Request with Parameters for Active Number of Calls and CallerID
    Status = LogHandler(request.args.get('active', type=str),request.args.get('callid', type=str),request.args.get('reason', type=str))
    #Do not add actual render page, the Snom tries to treat it like a settings file and dies. Super cool feature with no 
    return Response(status=200)
    
@app.route('/',methods=['POST','GET'])
def index():
    return Response(status=200)

if __name__ == "__main__":
    statuscheck = threading.Thread(target=CheckUp)
    statuscheck.start()
    app.run(host='172.27.66.107', port=62420, debug=False)
    
