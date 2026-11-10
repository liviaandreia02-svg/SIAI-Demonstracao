from flask import Flask,render_template,request,redirect,url_for,flash,Response,jsonify,abort
import sqlite3,csv,io,os,secrets
from datetime import datetime
app=Flask(__name__); app.secret_key=os.environ.get("APP_SECRET_KEY","troque-a-chave")
DB=os.environ.get("SIAI_DB_PATH",os.path.join("/tmp","siai_demo.db"))
TOKEN=os.environ.get("ESP32_API_TOKEN",secrets.token_urlsafe(32))

@app.before_request
def public_demo_read_only():
 if request.method not in ("GET", "HEAD", "OPTIONS"):
  abort(403)
 if request.path.startswith("/api/") or request.path == "/export.csv":
  abort(403)
def conn():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c
def init():
 with conn() as c:
  c.executescript("""CREATE TABLE IF NOT EXISTS rooms(id INTEGER PRIMARY KEY,name TEXT UNIQUE NOT NULL,description TEXT DEFAULT '');
  CREATE TABLE IF NOT EXISTS cabinets(id INTEGER PRIMARY KEY,name TEXT NOT NULL,room_id INTEGER NOT NULL,location TEXT DEFAULT '',active INTEGER DEFAULT 1,UNIQUE(name,room_id),FOREIGN KEY(room_id) REFERENCES rooms(id));
  CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,full_name TEXT NOT NULL,registration TEXT UNIQUE NOT NULL,biometric_id TEXT NOT NULL,room_id INTEGER NOT NULL,cabinet_id INTEGER NOT NULL,active INTEGER DEFAULT 1,created_at TEXT,FOREIGN KEY(room_id) REFERENCES rooms(id),FOREIGN KEY(cabinet_id) REFERENCES cabinets(id));
  CREATE TABLE IF NOT EXISTS logs(id INTEGER PRIMARY KEY,event_time TEXT NOT NULL,person_name TEXT,registration TEXT,biometric_id TEXT,room_name TEXT,cabinet_name TEXT,result TEXT,reason TEXT,source TEXT);""")
  if not c.execute("SELECT 1 FROM rooms LIMIT 1").fetchone():
   c.execute("INSERT INTO rooms(name,description) VALUES('Sala de exemplo','Registro demonstrativo')"); rid=c.execute("SELECT id FROM rooms").fetchone()["id"]
   c.execute("INSERT INTO cabinets(name,room_id,location) VALUES('Armário 01',?,'Demonstração')",(rid,)); cid=c.execute("SELECT id FROM cabinets").fetchone()["id"]
   c.execute("INSERT INTO users(full_name,registration,biometric_id,room_id,cabinet_id,created_at) VALUES(?,?,?,?,?,?)",("Usuário de demonstração","EXEMPLO-001","BIO-001",rid,cid,datetime.now().isoformat(timespec="seconds")))
   c.execute("INSERT INTO logs(event_time,person_name,registration,biometric_id,room_name,cabinet_name,result,reason,source) VALUES(?,?,?,?,?,?,?,?,?)",(datetime.now().astimezone().isoformat(timespec="seconds"),"Usuário de demonstração","EXEMPLO-001","BIO-001","Sala de exemplo","Armário 01","Autorizado","Registro fictício","Demonstração"))
@app.context_processor
def ctx(): return {"year":datetime.now().year}
@app.route("/")
def home():
 q=request.args.get("q","").strip()
 with conn() as c:
  stats=[c.execute("SELECT COUNT(*) FROM users WHERE active=1").fetchone()[0],c.execute("SELECT COUNT(*) FROM cabinets WHERE active=1").fetchone()[0],c.execute("SELECT COUNT(*) FROM logs WHERE date(event_time)=date('now','localtime')").fetchone()[0],c.execute("SELECT COUNT(*) FROM logs WHERE result='Negado'").fetchone()[0]]
  logs=c.execute("SELECT * FROM logs WHERE ?='' OR person_name LIKE ? OR registration LIKE ? ORDER BY event_time DESC LIMIT 12",(q,"%"+q+"%","%"+q+"%")).fetchall()
 return render_template("home.html",stats=stats,logs=logs,q=q)
@app.route("/users",methods=["GET","POST"])
def users():
 with conn() as c:
  if request.method=="POST":
   try:
    c.execute("INSERT INTO users(full_name,registration,biometric_id,room_id,cabinet_id,created_at) VALUES(?,?,?,?,?,?)",(request.form["name"].strip(),request.form["registration"].strip(),request.form["bio"].strip(),request.form["room"],request.form["cabinet"],datetime.now().isoformat(timespec="seconds")))
    flash("Usuário cadastrado.","success"); return redirect(url_for("users"))
   except (sqlite3.IntegrityError,KeyError): flash("Confira os campos. A matrícula precisa ser única.","error")
  us=c.execute("SELECT u.*,r.name room,c.name cabinet FROM users u JOIN rooms r ON r.id=u.room_id JOIN cabinets c ON c.id=u.cabinet_id ORDER BY u.full_name").fetchall()
  rooms=c.execute("SELECT * FROM rooms ORDER BY name").fetchall(); cabinets=c.execute("SELECT * FROM cabinets WHERE active=1 ORDER BY name").fetchall()
 return render_template("users.html",users=us,rooms=rooms,cabinets=cabinets)
@app.post("/users/<int:i>/toggle")
def toggle(i):
 with conn() as c:c.execute("UPDATE users SET active=1-active WHERE id=?",(i,))
 return redirect(url_for("users"))
@app.route("/rooms",methods=["GET","POST"])
def rooms():
 with conn() as c:
  if request.method=="POST":
   try:c.execute("INSERT INTO rooms(name,description) VALUES(?,?)",(request.form["name"].strip(),request.form.get("description","").strip())); flash("Sala cadastrada.","success")
   except sqlite3.IntegrityError:flash("Nome de sala já cadastrado.","error")
  rows=c.execute("SELECT r.*,COUNT(c.id) n FROM rooms r LEFT JOIN cabinets c ON c.room_id=r.id GROUP BY r.id").fetchall()
 return render_template("rooms.html",rooms=rows)
@app.route("/cabinets",methods=["GET","POST"])
def cabinets():
 with conn() as c:
  if request.method=="POST":
   try:c.execute("INSERT INTO cabinets(name,room_id,location) VALUES(?,?,?)",(request.form["name"].strip(),request.form["room"],request.form.get("location","").strip())); flash("Armário cadastrado.","success")
   except sqlite3.IntegrityError:flash("Confira o nome e a sala.","error")
  rows=c.execute("SELECT c.*,r.name room FROM cabinets c JOIN rooms r ON r.id=c.room_id ORDER BY r.name,c.name").fetchall(); rs=c.execute("SELECT * FROM rooms ORDER BY name").fetchall()
 return render_template("cabinets.html",cabinets=rows,rooms=rs)
@app.post("/cabinets/<int:i>/toggle")
def ctog(i):
 with conn() as c:c.execute("UPDATE cabinets SET active=1-active WHERE id=?",(i,))
 return redirect(url_for("cabinets"))
@app.route("/history")
def history():
 q=request.args.get("q","").strip(); result=request.args.get("result",""); start=request.args.get("start",""); end=request.args.get("end","")
 with conn() as c:
  logs=c.execute("""SELECT * FROM logs WHERE (?='' OR person_name LIKE ? OR registration LIKE ? OR biometric_id LIKE ? OR room_name LIKE ? OR cabinet_name LIKE ?) AND (?='' OR result=?) AND (?='' OR date(event_time)>=date(?)) AND (?='' OR date(event_time)<=date(?)) ORDER BY event_time DESC LIMIT 2000""",(q,"%"+q+"%","%"+q+"%","%"+q+"%","%"+q+"%","%"+q+"%",result,result,start,start,end,end)).fetchall()
 return render_template("history.html",logs=logs,q=q,result=result,start=start,end=end)
@app.route("/export.csv")
def export():
 q=request.args.get("q","").strip(); result=request.args.get("result",""); start=request.args.get("start",""); end=request.args.get("end","")
 with conn() as c: rows=c.execute("""SELECT event_time,person_name,registration,biometric_id,room_name,cabinet_name,result,reason,source FROM logs WHERE (?='' OR person_name LIKE ? OR registration LIKE ? OR biometric_id LIKE ? OR room_name LIKE ? OR cabinet_name LIKE ?) AND (?='' OR result=?) AND (?='' OR date(event_time)>=date(?)) AND (?='' OR date(event_time)<=date(?)) ORDER BY event_time DESC""",(q,"%"+q+"%","%"+q+"%","%"+q+"%","%"+q+"%","%"+q+"%",result,result,start,start,end,end)).fetchall()
 out=io.StringIO(); w=csv.writer(out,delimiter=";"); w.writerow(["Data e hora","Nome","Matrícula","ID biométrico","Sala","Armário","Resultado","Motivo","Origem"])
 for r in rows:w.writerow([r[k] or "" for k in ["event_time","person_name","registration","biometric_id","room_name","cabinet_name","result","reason","source"]])
 return Response("\\ufeff"+out.getvalue(),mimetype="text/csv; charset=utf-8",headers={"Content-Disposition":"attachment; filename=historico_acessos.csv"})
@app.post("/api/access")
def api_access():
 if not secrets.compare_digest(request.headers.get("X-API-Token",""),TOKEN):return jsonify(ok=False,error="Token inválido"),401
 d=request.get_json(silent=True) or {}; bio=str(d.get("biometric_id","")).strip(); result=d.get("result"); reason=str(d.get("reason",""))
 if not bio or result not in ("Autorizado","Negado"):return jsonify(ok=False,error="Envie biometric_id e result válido"),400
 with conn() as c:
  u=c.execute("SELECT u.*,r.name room,c.name cabinet FROM users u JOIN rooms r ON r.id=u.room_id JOIN cabinets c ON c.id=u.cabinet_id WHERE u.biometric_id=? AND u.active=1 AND c.active=1",(bio,)).fetchone()
  if result=="Autorizado" and (not u or (d.get("cabinet_id") is not None and str(u["cabinet_id"])!=str(d["cabinet_id"]))):result="Negado"; reason=reason or "ID não cadastrado, inativo ou armário incompatível"
  c.execute("INSERT INTO logs(event_time,person_name,registration,biometric_id,room_name,cabinet_name,result,reason,source) VALUES(?,?,?,?,?,?,?,?,?)",(datetime.now().astimezone().isoformat(timespec="seconds"),u["full_name"] if u else "Usuário não identificado",u["registration"] if u else "",bio,u["room"] if u else "",u["cabinet"] if u else "",result,reason,"ESP32"))
 return jsonify(ok=True,result=result,logged=True)
@app.post("/demo")
def demo():
 bio=request.form.get("bio",""); result=request.form.get("result","Negado")
 with conn() as c:
  u=c.execute("SELECT u.*,r.name room,c.name cabinet FROM users u JOIN rooms r ON r.id=u.room_id JOIN cabinets c ON c.id=u.cabinet_id WHERE biometric_id=?",(bio,)).fetchone()
  if result=="Autorizado" and (not u or not u["active"]):result="Negado"
  c.execute("INSERT INTO logs(event_time,person_name,registration,biometric_id,room_name,cabinet_name,result,reason,source) VALUES(?,?,?,?,?,?,?,?,?)",(datetime.now().astimezone().isoformat(timespec="seconds"),u["full_name"] if u else "Usuário não identificado",u["registration"] if u else "",bio,u["room"] if u else "",u["cabinet"] if u else "",result,"Demonstração; não veio do sensor físico","Demonstração"))
 flash("Evento demonstrativo registrado.","success");return redirect(url_for("history"))
if __name__=="__main__":
 init();app.run(host="127.0.0.1",port=5000,debug=False)
