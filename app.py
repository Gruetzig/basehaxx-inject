from flask import Flask, render_template, request, make_response
import os
import subprocess
import struct
import hashlib

app = Flask(__name__)

boot9loc = os.path.join(os.path.expanduser("~"), ".3ds", "boot9.bin")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/save_in_out", methods = ['POST'])
def do_save():
    print("hey")
    game = request.form['oras']
    model = request.form['model']
    region = request.form['region']
    if not game in {"or", "as"}:
        return "<p>Invalid game</p>"
    if not model in {"new", "old"}:
        return "<p>Invalid model</p>"
    if not region in {"eur", "usa", "jpn"}:
        "<p>Invalid region</p>"
    insave = request.files['save']
    movable = request.files['movable']
    insave.save(os.path.join(app.root_path, 'activejob/00000001.sav'))
    insave.seek(0)
    insave.save(os.path.join(app.root_path, 'activejob/00000001.sav.bak'))
    movable.save(os.path.join(app.root_path, "activejob/movable.sed"))

    # start job
    basepath = os.path.join(app.root_path, 'activejob')
    savespath = os.path.join(app.root_path, 'saves')
    print(f"New job for {game} {model} {region}")
    with open(f"{basepath}/movable.sed", "rb") as movablef:
        id0 = struct.pack('>IIII', *struct.unpack('<IIII', hashlib.sha256(movablef.read()[0x110:0x120]).digest()[0:16])).hex()
    curid0 = os.listdir(f"{basepath}/Nintendo 3DS")[0]
    # rename current id0 to target id0
    os.rename(f"{basepath}/Nintendo 3DS/{curid0}", f"{basepath}/Nintendo 3DS/{id0}")
    if game == "or":
        tid = "0011c400"
    else:
        tid = "0011c500" 
    # move save
    os.rename(f"{basepath}/00000001.sav", f"{basepath}/Nintendo 3DS/{id0}/00000000000000000000000000000000/title/00040000/{tid}/data/00000001.sav")
    
    # save3ds-fuse
    if not 'archive' in os.listdir(basepath):
        os.mkdir(f"{basepath}/archive/")
    # save3ds_fuse --movable movable.bin --boot9 boot9.bin --sd D:\ --sdsave 0004000000030800 -x out
    command = [f"{app.root_path}/bin/save3ds_fuse", "--movable", f"{basepath}/movable.sed", "--boot9", boot9loc, "--sd", f"{basepath}/.", "--sdsave", f"00040000{tid}", "-x", f"{basepath}/archive/"]
    print(command)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    print(stdout)
    print(stderr)
    if not os.path.isfile(f"{basepath}/archive/main"):
        return "<p>Failed to open save file</p>"
    # read original saves secure value
    with open(f"{basepath}/archive/main", "rb") as file:
        file.seek(0x75C00)
        securevalue = file.read(8)

    # write to save
    with open(f"{basepath}/archive/main", "wb") as file:
        with open(f"{savespath}/{game}-{region}-{model}", "rb") as otherfile:
            file.write(otherfile.read())
        file.seek(0x75C00)
        file.write(securevalue)
    
    command = [f"{app.root_path}/bin/save3ds_fuse", "--movable", f"{basepath}/movable.sed", "--boot9", boot9loc, "--sd", f"{basepath}", "-i", f"{basepath}/archive"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    print(stdout)
    print(stderr)
    
    command = ["bin/zip_contents.sh", f"{basepath}/Nintendo 3DS/{id0}/00000000000000000000000000000000/title/00040000/{tid}/data/00000001.sav", "activejob/00000001.sav.bak", f"{basepath}/{game}_save.zip"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    print(stdout)
    print(stderr)

    with open(f"{basepath}/{game}_save.zip", "rb") as zipf:
        zip = zipf.read()
    response = make_response(zip)
    response.headers.set('Content-Type', 'application/octet-stream')
    response.headers.set('Content-Disposition', 'attachment', filename=f'{game}_save.zip')
    os.remove(f"{basepath}/{game}_save.zip")
    for f in os.listdir(f"{basepath}/archive"):
        os.remove(os.path.join(f"{basepath}/archive", f))
    os.remove(f"{basepath}/movable.sed")
    os.remove(f"{basepath}/00000001.sav.bak")
    os.remove(f"{basepath}/Nintendo 3DS/{id0}/00000000000000000000000000000000/title/00040000/{tid}/data/00000001.sav")
    return response
