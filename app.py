import asyncio
import base64
import secrets
import websockets
import json
import hashlib
import re
import uuid
from database import add_key, retrieve, rename, edit, delete, dump
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

MIME_APP_PASSWORD = "annoznobpygmtuxu"
SENDER = "nedis232250@gmail.com"
DONATION_LINK = "youtube.com/@Nedis232"

"""

kv.txt stores user data
posts.txt stores key value data like website posts, blog posts, MOTD
animals.txt stores animal data
adoptions.txt stores

TODO:

Natural disaster/human disaster

FOCUS FOCUS FOCUS FOCUS FOCUS FOCUS FOCUS FOCUS FOCUS FOCUS FOCUS FOCUS FOCUS FOCUS FOCUS FOCUS FOCUS FOCUS FOCUS FOCUS FOCUS FOCUS FOCUS FOCUS FOCUS:
Adoption

Format for volunteering:

["hh:mm,dd/mm/yyyy-hh:mm,dd/mm/yyyy,#", ["email"...]] (repeat)
["01:30pm,3/4/2026-02:30pm,3/4/2026,2", ["nedis232250@gmail.com"]] -- 1:30pm march 4th 2026-2:30pm march 4th 2026, 2 people can volunteer


Format for adoptions:

["hh:mm,dd/mm/yyyy", "email"] (only 1)
["2:40pm,6/19/2027", "nedis232250@gmail.com"] -- 2:40pm june 19th 2027 for nedis232250@gmail.com

"""

async def handler(ws):
    async for msg in ws:
        print("Got:", msg)
        try:
            cmd = json.loads(msg)

            if cmd["instruction"] == "add user":
                success = True
                errormsg = ""

                if len(cmd["password"]) < 9:
                    success = False
                    errormsg = "Password must be at least 8 characters long"
                if len(cmd["password"]) > 60:
                    success = False
                    errormsg = "Password must be less than 60 characters long (for storage reasons)"
                elif not re.search(r"[A-Z]", cmd["password"]):
                    success = False
                    errormsg = "Password must contain an uppercase letter"
                elif not re.search(r"[a-z]", cmd["password"]):
                    success = False
                    errormsg = "Password must contain a lowercase letter"
                elif not re.search(r"[0-9]", cmd["password"]):
                    success = False
                    errormsg = "Password must contain a number"
                elif not re.search(r"[`~!@#$%^&*()_\-\+={}\[\]|\\;:\"'/?.>,<]", cmd["password"]):
                    success = False
                    errormsg = "Password must contain a special character"
                elif not re.search(r"^[^@ \t\r\n,]+@[^@ \t\r\n,]+\.[^@ \t\r\n,]+$", cmd["email"].strip()):
                    success = False
                    errormsg = "Email is in wrong configuration"
                elif re.search(r"[,]", cmd["email"].strip()):
                    success = False
                    errormsg = "Email must not contain a comma"
                elif len(cmd["email"].strip()) > 256:
                    success = False
                    errormsg = "Email may not be more than 256 characters (for storage reasons)"

                if success:
                    user_metadata = {
                        "password": hashlib.sha256(cmd["password"].encode()).hexdigest(),
                        "sessionID": 0,
                        "bio": "",
                        "role": "user",
                        "verified": False,
                        "volunteering": {},
                        "adoptions": {},
                        "relinquishments": {},
                        "user data": {"verificationQ": {}}
                    }

                    if add_key(cmd["email"].strip(), json.dumps(user_metadata), "kv.txt") == "Key is already created!":
                        success = False
                        errormsg = "The email you tried to sign up with is already registered!"

                return_signup = {
                    "server response": "return signup",
                    "success": success,
                    "errormsg": errormsg
                }

                await ws.send(json.dumps(return_signup))
            elif cmd["instruction"] == "login":
                success = True
                errormsg = ""
                rk = retrieve(cmd["email"].strip(), "kv.txt")
                nsid = 0

                if rk == "Key does not exist!":
                    errormsg = "Email or password is incorrect!"
                    success = False
                else:
                    if json.loads(rk)["password"] == hashlib.sha256(cmd["password"].encode()).hexdigest():
                        user_metadata = json.loads(rk)
                        user_metadata["sessionID"] = str(uuid.uuid4())
                        nsid = user_metadata["sessionID"]

                        edit(cmd["email"].strip(), json.dumps(user_metadata), "kv.txt")
                    else:
                        errormsg = "Email or password is incorrect!"
                        success = False

                return_login = {
                    "server response": "return login",
                    "success": success,
                    "errormsg": errormsg,
                    "sessionID": nsid if success else ""
                }

                await ws.send(json.dumps(return_login))
            elif cmd["instruction"] == "pwchange":
                success = True
                errormsg = ""
                rk = retrieve(cmd["email"].strip(), "kv.txt")

                if rk == "Key does not exist!":
                    errormsg = "Email or password is incorrect!"
                    success = False
                else:
                    if json.loads(rk)["password"] == hashlib.sha256(cmd["old"].encode()).hexdigest():
                        if len(cmd["new"]) < 9:
                            success = False
                            errormsg = "Password must be at least 8 characters long"
                        if len(cmd["new"]) > 30:
                            success = False
                            errormsg = "Password must be less than 30 characters long (for storage reasons)"
                        elif not re.search(r"[A-Z]", cmd["new"]):
                            success = False
                            errormsg = "Password must contain an uppercase letter"
                        elif not re.search(r"[a-z]", cmd["new"]):
                            success = False
                            errormsg = "Password must contain a lowercase letter"
                        elif not re.search(r"[0-9]", cmd["new"]):
                            success = False
                            errormsg = "Password must contain a number"
                        elif not re.search(r"[`~!@#$%^&*()_\-\+={}\[\]|\\;:\"'/?.>,<]", cmd["new"]):
                            success = False
                            errormsg = "Password must contain a special character"
                        else:
                            user_metadata = json.loads(rk)
                            user_metadata["password"] = hashlib.sha256(cmd["new"].encode()).hexdigest()

                            edit(cmd["email"].strip(), json.dumps(user_metadata), "kv.txt")
                    else:
                        return_pwchange = {
                            "server response": "return pwchange",
                            "success": success,
                            "errormsg": errormsg,
                        }

                        await ws.send(json.dumps(return_pwchange))
            elif cmd["instruction"] == "delete user":
                success = True
                errormsg = ""
                rk = retrieve(cmd["email"].strip(), "kv.txt")

                if rk == "Key does not exist!":
                    errormsg = "Email or password is incorrect!"
                    success = False
                else:
                    if json.loads(rk)["password"] == hashlib.sha256(cmd["password"].encode()).hexdigest():
                        delete(cmd["email"].strip(), "kv.txt")
                    else:
                        errormsg = "Email or password is incorrect!"
                        success = False

                return_deluser = {
                    "server response": "return deluser",
                    "success": success,
                    "errormsg": errormsg,
                }

                await ws.send(json.dumps(return_deluser))
            elif cmd["instruction"] == "send veri":
                success = True
                errormsg = ""
                rk = retrieve(cmd["email"].strip(), "kv.txt")

                if rk != "Key does not exist!":
                    vcode = secrets.randbelow(900000) + 100000
                    msg = MIMEText("Your verification code: " + str(vcode) + " it expires in 20 minutes!")
                    msg["Subject"] = "Verify Your Email"
                    msg["From"] = SENDER
                    msg["To"] = cmd["email"].strip()

                    # Connect to Gmail SMTP with app password
                    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                        server.login(SENDER, MIME_APP_PASSWORD)  # use the app password
                        server.send_message(msg)
                        user_metadata = json.loads(rk)
                        user_metadata["user data"]["verificationQ"] = { "vcode": str(vcode), "expires": (datetime.now() + timedelta(minutes=20)).isoformat() }
                        edit(cmd["email"].strip(), json.dumps(user_metadata), "kv.txt")
                else:
                    success = False
                    errormsg = "Email does not exist!"

                return_verification = {
                    "server response": "verification email sent",
                    "success": success,
                    "errormsg": errormsg
                }
                
                await ws.send(json.dumps(return_verification))
            elif cmd["instruction"] == "verify user":
                success = True
                errormsg = ""
                rk = retrieve(cmd["email"].strip(), "kv.txt")

                if rk == "Key does not exist!":
                    success = False
                    errormsg = "Email does not exist!"
                else:
                    if cmd["code"] == json.loads(rk)["user data"]["verificationQ"]["vcode"]:
                        if datetime.now() > datetime.fromisoformat(json.loads(rk)["user data"]["verificationQ"]["expires"]):
                            success = False
                            errormsg = "Verification code is incorrect or expired!"
                            break

                        user_metadata = json.loads(rk)
                        user_metadata["user data"]["verificationQ"] = {}
                        user_metadata["verified"] = True
                        edit(cmd["email"].strip(), json.dumps(user_metadata), "kv.txt")
                    else:
                        success = False
                        errormsg = "Verification code is incorrect or expired!"

                return_verification = {
                    "server response": "user verification",
                    "success": success,
                    "errormsg": errormsg
                }
                
                await ws.send(json.dumps(return_verification))
            elif cmd["instruction"] == "logout":
                success = True
                errormsg = ""

                if cmd["sessionID"].strip() == json.loads(retrieve(cmd["email"].strip(), "kv.txt"))["sessionID"]:
                    user_metadata = json.loads(retrieve(cmd["email"].strip(), "kv.txt"))
                    user_metadata["sessionID"] = 0
                    edit(cmd["email"].strip(), json.dumps(user_metadata), "kv.txt")
                else:
                    success = False
                    errormsg = "SessionID does not match the email. Can not log you out!"
                
                return_logout = {
                    "server_response": "user logout",
                    "success": success,
                    "errormsg": errormsg
                }

                await ws.send(json.dumps(return_logout))
            elif cmd["instruction"] == "add animal":
                success = True
                errormsg = ""
                users = dump("kv.txt")
                correct_user_dat = ""

                for user in users:
                    user_metadata = json.loads(user.split(",", 1)[1].strip())

                    if str(cmd["sessionID"]).strip() == 0:
                        break

                    if user_metadata["sessionID"] == cmd["sessionID"]:
                        correct_user_dat = user_metadata
                        
                        if correct_user_dat["role"] == "staff" or correct_user_dat["role"] == "admin":
                            if add_key(cmd["name"], json.dumps({"name": cmd["name"], "age": cmd["age"], "sex": cmd["sex"], "reproductive organs": cmd["RO"], "animal and breed": cmd["A+B"], "vaccinations": cmd["vaccinations"], "needs": cmd["needs"], "preferences": cmd["preferences"], "length/height and weight": cmd["hw"], "pictures": cmd["pictures"], "history": cmd["history"]}), "animals.txt") == "Key is already created!":
                                success = False
                                errormsg = "Animal is already registered!"
                            else:
                                edit("space", str(int(retrieve("space", "misc.txt")) - 1), "misc.txt")
                        else:
                            success = False
                            errormsg = "Session ID does not exist or you are not an administrator or staff"
                        
                        break
                else:
                    success = False
                    errormsg = "Session ID does not exist or you are not an administrator or staff"

                return_add_animal = {
                    "server response": "add animal",
                    "success": success,
                    "errormsg": errormsg
                }
                
                await ws.send(json.dumps(return_add_animal))
            elif cmd["instruction"] == "edit animal":
                success = True
                errormsg = ""
                users = dump("kv.txt")
                correct_user_dat = ""

                for user in users:
                    user_metadata = json.loads(user.split(",", 1)[1].strip())

                    if str(cmd["sessionID"]).strip() == 0:
                        break

                    if user_metadata["sessionID"] == cmd["sessionID"]:
                        correct_user_dat = user_metadata
                        
                        if correct_user_dat["role"] == "staff" or correct_user_dat["role"] == "admin":
                            if edit(cmd["name"], json.dumps({"name": cmd["name"], "age": cmd["age"], "sex": cmd["sex"], "reproductive organs": cmd["RO"], "animal and breed": cmd["A+B"], "vaccinations": cmd["vaccinations"], "needs": cmd["needs"], "preferences": cmd["preferences"], "length/height and weight": cmd["hw"], "pictures": cmd["pictures"], "history": cmd["history"]}), "animals.txt") == "Key does not exist!":
                                success = False
                                errormsg = "Animal does not exist!"
                        else:
                            success = False
                            errormsg = "Session ID does not exist or you are not an administrator or staff"
                        
                        break
                else:
                    success = False
                    errormsg = "Session ID does not exist or you are not an administrator or staff"
                
                
                return_edit_animal = {
                    "server response": "edit animal",
                    "success": success,
                    "errormsg": errormsg
                }
                
                await ws.send(json.dumps(return_edit_animal))
            elif cmd["instruction"] == "delete animal":
                success = True
                errormsg = ""
                users = dump("kv.txt")
                correct_user_dat = ""

                for user in users:
                    user_metadata = json.loads(user.split(",", 1)[1].strip())

                    if str(cmd["sessionID"]).strip() == 0:
                        break

                    if user_metadata["sessionID"] == cmd["sessionID"]:
                        correct_user_dat = user_metadata
                        
                        if correct_user_dat["role"] == "staff" or correct_user_dat["role"] == "admin":
                            if delete(cmd["name"], "animals.txt") == "Key does not exist!":
                                success = False
                                errormsg = "Animal does not exist!"
                            else:
                                edit("space", str(int(retrieve("space", "misc.txt")) + 1), "misc.txt")
                        else:
                            success = False
                            errormsg = "Session ID does not exist or you are not an administrator or staff"
                        
                        break
                else:
                    success = False
                    errormsg = "Session ID does not exist or you are not an administrator or staff"

                return_delete_animal = {
                    "server response": "delete animal",
                    "success": success,
                    "errormsg": errormsg
                }
                    
                await ws.send(json.dumps(return_delete_animal))
            elif cmd["instruction"] == "request animals":
                await ws.send(dump("animals.txt"))
            elif cmd["instruction"] == "request animal":
                await ws.send(retrieve(cmd["name"].strip(), "animals.txt"))
            elif cmd["instruction"] == "donate":
                await ws.send(DONATION_LINK)
            elif cmd["instruction"] == "add key":
                success = True
                errormsg = ""
                users = dump("kv.txt")
                correct_user_dat = ""

                for user in users:
                    user_metadata = json.loads(user.split(",", 1)[1].strip())

                    if str(cmd["sessionID"]).strip() == 0:
                        break

                    if user_metadata["sessionID"] == cmd["sessionID"]:
                        correct_user_dat = user_metadata
                        
                        if correct_user_dat["role"] == "staff" or correct_user_dat["role"] == "admin":
                            add_key(cmd["key"], cmd["data"], "posts.txt")
                        else:
                            success = False
                            errormsg = "Session ID does not exist or you are not an administrator or staff"
                        
                        break
                else:
                    success = False
                    errormsg = "Session ID does not exist or you are not an administrator or staff"

                return_add_key = {
                    "server response": "add key",
                    "success": success,
                    "errormsg": errormsg
                }
                    
                await ws.send(json.dumps(return_add_key))
            elif cmd["instruction"] == "edit key":
                success = True
                errormsg = ""
                users = dump("kv.txt")
                correct_user_dat = ""

                for user in users:
                    user_metadata = json.loads(user.split(",", 1)[1].strip())

                    if str(cmd["sessionID"]).strip() == 0:
                        break

                    if user_metadata["sessionID"] == cmd["sessionID"]:
                        correct_user_dat = user_metadata
                        
                        if correct_user_dat["role"] == "staff" or correct_user_dat["role"] == "admin":
                            edit(cmd["key"], cmd["data"], "posts.txt")
                        else:
                            success = False
                            errormsg = "Session ID does not exist or you are not an administrator or staff"
                        
                        break
                else:
                    success = False
                    errormsg = "Session ID does not exist or you are not an administrator or staff"

                return_edit_key = {
                    "server response": "edit key",
                    "success": success,
                    "errormsg": errormsg
                }
                    
                await ws.send(json.dumps(return_edit_key))
            elif cmd["instruction"] == "delete key":
                success = True
                errormsg = ""
                users = dump("kv.txt")
                correct_user_dat = ""

                for user in users:
                    user_metadata = json.loads(user.split(",", 1)[1].strip())

                    if str(cmd["sessionID"]).strip() == 0:
                        break

                    if user_metadata["sessionID"] == cmd["sessionID"]:
                        correct_user_dat = user_metadata
                        
                        if correct_user_dat["role"] == "staff" or correct_user_dat["role"] == "admin":
                            delete(cmd["key"], "posts.txt")
                        else:
                            success = False
                            errormsg = "Session ID does not exist or you are not an administrator or staff"
                        
                        break
                else:
                    success = False
                    errormsg = "Session ID does not exist or you are not an administrator or staff"

                return_delete_key = {
                    "server response": "delete key",
                    "success": success,
                    "errormsg": errormsg
                }
                    
                await ws.send(json.dumps(return_delete_key))
            elif cmd["instruction"] == "get key":
                await ws.send(json.dumps({"server response": "get key", "data": retrieve(cmd["key"], "posts.txt"), "for": cmd["for"]}))
            elif cmd["instruction"] == "create volunteering":
                success = True
                errormsg = ""
                users = dump("kv.txt")
                correct_user_dat = ""

                for user in users:
                    user_metadata = json.loads(user.split(",", 1)[1].strip())

                    if str(cmd["sessionID"]).strip() == 0:
                        break

                    if user_metadata["sessionID"] == cmd["sessionID"]:
                        correct_user_dat = user_metadata
                        
                        if correct_user_dat["role"] == "staff" or correct_user_dat["role"] == "admin":
                            add_key(cmd["name"], json.dumps({"header": cmd["header"], "desc": cmd["desc"], "pictures": cmd["pictures"], "hours": cmd["hours"]}), "volunteers.txt")
                        else:
                            success = False
                            errormsg = "Session ID does not exist or you are not an administrator or staff"
                        
                        break
                else:
                    success = False
                    errormsg = "Session ID does not exist or you are not an administrator or staff"

                return_add_volunteer = {
                    "server response": "add volunteer",
                    "success": success,
                    "errormsg": errormsg
                }

                await ws.send(json.dumps(return_add_volunteer))
            elif cmd["instruction"] == "volunteer":
                success = True
                errormsg = ""
                users = dump("kv.txt")
                correct_user_dat = ""
                correct_user_email = ""

                for user in users:
                    user_metadata = json.loads(user.split(",", 1)[1].strip())

                    if user_metadata["sessionID"] == cmd["sessionID"]:
                        correct_user_dat = user_metadata
                        correct_user_email = user.split(",", 1)[0].strip()

                        if retrieve(cmd["name"], "volunteers.txt") == "Key does not exist!":
                            success = False
                            errormsg = "Volunteer session does not exist!"

                            break

                        name = json.loads(retrieve(cmd["name"], "volunteers.txt"))
                        hours = name["hours"]

                        for i in range(len(hours)):
                            if i % 2 == 0:
                                if hours[i] == cmd["hours"]:
                                    volunteered = False

                                    for v in hours[i + 1]:
                                        if v == correct_user_email:
                                            volunteered = True
                                    
                                    if int(hours[i].split(",")[3]) == len(hours[i + 1]):
                                        success = False
                                        errormsg = "Max capacity reached!"
                                    elif not volunteered:
                                        hours[i + 1].append(correct_user_email)
                                        name["hours"] = hours
                                        edit(cmd["name"], json.dumps(name), "volunteers.txt")
                                    else:
                                        success = False
                                        errormsg = "You are already volunteered for this!"
                
                if correct_user_dat == "" or correct_user_email == "":
                    success = False
                    errormsg = "SessionID does not exist!"

                return_volunteer = {
                    "server response": "volunteer",
                    "success": success,
                    "errormsg": errormsg
                }

                await ws.send(json.dumps(return_volunteer))
            elif cmd["instruction"] == "edit volunteer":
                success = True
                errormsg = ""
                users = dump("kv.txt")
                correct_user_dat = ""

                for user in users:
                    user_metadata = json.loads(user.split(",", 1)[1].strip())

                    if str(cmd["sessionID"]).strip() == 0:
                        break

                    if user_metadata["sessionID"] == cmd["sessionID"]:
                        correct_user_dat = user_metadata
                        
                        if correct_user_dat["role"] == "staff" or correct_user_dat["role"] == "admin":
                            edit(cmd["name"], json.dumps({"header": cmd["header"], "desc": cmd["desc"], "pictures": cmd["pictures"], "hours": cmd["hours"]}), "volunteers.txt")
                        else:
                            success = False
                            errormsg = "Session ID does not exist or you are not an administrator or staff"
                        
                        break
                else:
                    success = False
                    errormsg = "Session ID does not exist or you are not an administrator or staff"

                return_edit_volunteer = {
                    "server response": "edit volunteer",
                    "success": success,
                    "errormsg": errormsg
                }

                await ws.send(json.dumps(return_edit_volunteer))
            elif cmd["instruction"] == "delete volunteer":
                success = True
                errormsg = ""
                users = dump("kv.txt")
                correct_user_dat = ""

                for user in users:
                    user_metadata = json.loads(user.split(",", 1)[1].strip())

                    if str(cmd["sessionID"]).strip() == "0":
                        break

                    if user_metadata["sessionID"] == cmd["sessionID"]:
                        correct_user_dat = user_metadata
                        
                        if correct_user_dat["role"] == "staff" or correct_user_dat["role"] == "admin":
                            delete(cmd["name"], "volunteers.txt")
                        else:
                            success = False
                            errormsg = "Session ID does not exist or you are not an administrator or staff"
                        
                        break
                else:
                    success = False
                    errormsg = "Session ID does not exist or you are not an administrator or staff"

                return_delete_volunteer = {
                    "server response": "edit volunteer",
                    "success": success,
                    "errormsg": errormsg
                }

                await ws.send(json.dumps(return_delete_volunteer))
            elif cmd["instruction"] == "request volunteers":
                await ws.send(dump("volunteers.txt"))
            elif cmd["instruction"] == "request volunteer":
                await ws.send(retrieve(cmd["name"], "volunteers.txt"))
            elif cmd["instruction"] == "request capacity":
                await ws.send(json.dumps({"server response": "return capacity", "capacity": retrieve("space", "misc.txt")}))
            elif cmd["instruction"] == "set capacity":
                success = True
                errormsg = ""
                users = dump("kv.txt")
                correct_user_dat = ""

                for user in users:
                    user_metadata = json.loads(user.split(",", 1)[1].strip())

                    if str(cmd["sessionID"]).strip() == 0:
                        break

                    if user_metadata["sessionID"] == cmd["sessionID"]:
                        correct_user_dat = user_metadata
                        
                        if correct_user_dat["role"] == "staff" or correct_user_dat["role"] == "admin":
                            edit("space", cmd["space"], "misc.txt")
                        else:
                            success = False
                            errormsg = "Session ID does not exist or you are not an administrator or staff"
                        
                        break
                else:
                    success = False
                    errormsg = "Session ID does not exist or you are not an administrator or staff"

                return_edit_space = {
                    "server response": "edit space",
                    "success": success,
                    "errormsg": errormsg
                }

                await ws.send(json.dumps(return_edit_space))
            elif cmd["instruction"] == "add adoption":
                success = True
                errormsg = ""
                users = dump("kv.txt")
                correct_user_dat = ""

                for user in users:
                    user_metadata = json.loads(user.split(",", 1)[1].strip())

                    if str(cmd["sessionID"]).strip() == 0:
                        break

                    if user_metadata["sessionID"] == cmd["sessionID"]:
                        correct_user_dat = user_metadata
                        
                        if correct_user_dat["role"] == "staff" or correct_user_dat["role"] == "admin":
                            if retrieve(cmd["name"], "animals.txt") == "Key does not exist!":
                                success = False
                                errormsg = "Animal does not exist!"
                            elif retrieve(cmd["name"], "adoptions.txt") != "Key does not exist!":
                                success = False
                                errormsg = "Animal is already in the database!"
                            else:
                                add_key(cmd["name"], json.dumps({ "header": cmd["header"], "desc": cmd["desc"], "pictures": cmd["pictures"], "hours": cmd["hours"] }), "adoptions.txt")
                        else:
                            success = False
                            errormsg = "Session ID does not exist or you are not an administrator or staff"
                        
                        break
                else:
                    success = False
                    errormsg = "Session ID does not exist or you are not an administrator or staff"

                return_add_adoption = {
                    "server response": "add adoption",
                    "success": success,
                    "errormsg": errormsg
                }

                await ws.send(json.dumps(return_add_adoption))
            elif cmd["instruction"] == "delete adoption":
                success = True
                errormsg = ""
                users = dump("kv.txt")
                correct_user_dat = ""

                for user in users:
                    user_metadata = json.loads(user.split(",", 1)[1].strip())

                    if str(cmd["sessionID"]).strip() == 0:
                        break

                    if user_metadata["sessionID"] == cmd["sessionID"]:
                        correct_user_dat = user_metadata
                        
                        if correct_user_dat["role"] == "staff" or correct_user_dat["role"] == "admin":
                            if retrieve(cmd["name"], "adoptions.txt") == "Key does not exist!":
                                success = False
                                errormsg = "Animal does not exist!"
                            else:
                                delete(cmd["name"], "adoptions.txt")
                        else:
                            success = False
                            errormsg = "Session ID does not exist or you are not an administrator or staff"
                        break
                else:
                    success = False
                    errormsg = "Session ID does not exist or you are not an administrator or staff"

                return_delete_adoption = {
                    "server response": "delete adoption",
                    "success": success,
                    "errormsg": errormsg
                }

                await ws.send(json.dumps(return_delete_adoption))
            elif cmd["instruction"] == "adopt":
                success = True
                errormsg = ""
                correct_user_dat = ""
                correct_user_email = ""
                users = dump("kv.txt")

                for user in users:
                    user_metadata = json.loads(user.split(",", 1)[1].strip())

                    if user_metadata["sessionID"] == cmd["sessionID"]:
                        correct_user_dat = user_metadata
                        correct_user_email = user.split(",", 1)[0].strip()
                        
                        if retrieve(cmd["name"], "adoptions.txt") == "Key does not exist!":
                            success = False
                            errormsg = "Adoption session does not exist!"

                            break

                        hour_data = json.loads(retrieve(cmd["name"].strip(), "adoptions.txt"))
                        hours = hour_data["hours"]

                        for i in range(len(hours)):
                            if i % 2 == 0:
                                if hours[i] == cmd["hours"]: # Found match
                                    if hours[i + 1] == correct_user_email:
                                        success = False
                                        errormsg = "You are already signed up for this!"
                                    elif hours[i + 1] != "":
                                        success = False
                                        errormsg = "Session is already booked!"
                                    elif hours[i + 1] == "":
                                        hours[i + 1] = correct_user_email
                                        hour_data["hours"] = hours
                                        edit(cmd["name"], json.dumps(hour_data), "adoptions.txt")

                if correct_user_email == "" or correct_user_dat == "":
                    success = False
                    errormsg = "sessionID does not exist!"

                return_adopt = {
                    "server response": "adopt",
                    "success": success,
                    "errormsg": errormsg,
                }

                await ws.send(json.dumps(return_adopt))
            elif cmd["instruction"] == "image":
                with open("pictures/" + cmd["path"], "rb") as f:
                    img_bytes = f.read()
                
                encoded_image = base64.b64encode(img_bytes).decode("utf-8")
            
                return_image = {
                    "server response": "image",
                    "data": encoded_image,
                    "for": cmd["for"]
                }

                await ws.send(json.dumps(return_image))
                                
        except Exception as e:
            await ws.send("Error: " + str(e))

async def main():

    async with websockets.serve(handler, "localhost", 8765, max_size=2097152):
        print("WebSocket open on ws://localhost:8765")
        await asyncio.Future()

asyncio.run(main())

input()
