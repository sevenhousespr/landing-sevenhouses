from flask import Flask, render_template, request
from fpdf import FPDF
from datetime import datetime
import os
import smtplib
from email.message import EmailMessage

app = Flask(__name__)

DATA_DIR = "data"
PDF_DIR = os.path.join(DATA_DIR, "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)

# ========= CONFIGURAZIONE EMAIL (DA PERSONALIZZARE) =========
SMTP_HOST = "smtp.mail.me.com"     # es: smtp.gmail.com
SMTP_PORT = 587                      # 465 o 587 in base al provider
SMTP_USER = "seven.houses@icloud.com"
SMTP_PASS = "kjic-ymtx-csis-hzzt"
EMAIL_TUA = "seven.houses@icloud.com"     # dove arrivano i lead


def calcola_preventivo(data):
    """Calcolo preventivo ristrutturazione orientato a cliente finale (solo per uso interno)."""
    mq = data.get("mq", 0)
    n_bagni = data.get("bagni", 0)
    rifare_bagni = data.get("rifare_bagni", False)
    n_finestre = data.get("finestre", 0)
    rifare_finestre = data.get("rifare_finestre", False)
    n_portefinestre = data.get("portefinestre", 0)
    rifare_portefinestre = data.get("rifare_portefinestre", False)
    rifare_impianto = data.get("rifare_impianto", False)
    rifare_pavimenti = data.get("rifare_pavimenti", False)
    tinteggio = data.get("tinteggio", False)
    extra_importo = data.get("extra_importo", 0)
    budget_generico = data.get("budget_generico", 0)

    # Prezzi standard interni
    costo_bagno = 7500
    costo_finestra = 800
    costo_portafinestra = 1000
    costo_impianto = 6000
    costo_pavimenti_mq = 50
    costo_tinteggio_mq = 12

    costo_bagni = n_bagni * costo_bagno if rifare_bagni else 0
    costo_finestre = n_finestre * costo_finestra if rifare_finestre else 0
    costo_portefinestre = n_portefinestre * costo_portafinestra if rifare_portefinestre else 0
    costo_impianto_tot = costo_impianto if rifare_impianto else 0
    costo_pavimenti = mq * costo_pavimenti_mq if rifare_pavimenti else 0
    costo_tinteggio = mq * costo_tinteggio_mq if tinteggio else 0

    totale_lavori = (
        budget_generico
        + costo_bagni
        + costo_finestre
        + costo_portefinestre
        + costo_impianto_tot
        + costo_pavimenti
        + costo_tinteggio
        + extra_importo
    )

    return {
        "costo_bagni": round(costo_bagni),
        "costo_finestre": round(costo_finestre),
        "costo_portefinestre": round(costo_portefinestre),
        "costo_impianto": round(costo_impianto_tot),
        "costo_pavimenti": round(costo_pavimenti),
        "costo_tinteggio": round(costo_tinteggio),
        "extra_importo": round(extra_importo),
        "budget_generico": round(budget_generico),
        "totale_lavori": round(totale_lavori),
    }


def genera_pdf_preventivo(data, risultati):
    """Genera un PDF interno con il preventivo ristrutturazione (solo per Seven Houses)."""
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=12)

    pdf.set_font("Arial", "", 10)

    blu = (0, 70, 140)
    grigio = (90, 90, 90)

    # HEADER CON LOGO (se presente)
    try:
        pdf.image("Tavola disegno 1.png", x=10, y=10, w=30)
    except Exception:
        pass

    pdf.set_xy(45, 12)
    pdf.set_text_color(*blu)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 8, "Seven Houses", ln=1)

    pdf.set_x(45)
    pdf.set_text_color(*grigio)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, "Preventivo indicativo ristrutturazione (uso interno)", ln=1)

    pdf.ln(6)

    def section_title(testo):
        pdf.set_text_color(*blu)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 7, testo, ln=1)
        pdf.set_draw_color(*blu)
        pdf.set_line_width(0.4)
        y = pdf.get_y()
        pdf.line(10, y, 200, y)
        pdf.ln(3)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "", 10)

    def row(label, value):
        pdf.set_font("Arial", "B", 10)
        pdf.cell(80, 6, str(label), border=0)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 6, str(value), ln=1, border=0)

    # SEZIONE CLIENTE
    section_title("Dati cliente")
    row("Nome", data.get("nome", ""))
    row("Cognome", data.get("cognome", ""))
    row("Email", data.get("email", ""))
    row("Telefono", data.get("telefono", ""))

    # SEZIONE IMMOBILE
    section_title("Dati immobile")
    row("Comune / Zona", data.get("zona", ""))
    row("Indirizzo", data.get("indirizzo", ""))
    row("Metri quadri", f"{data.get('mq', 0)} mq")

    # SEZIONE LAVORI
    section_title("Lavori richiesti e costi stimati")

    row("Numero bagni", data.get("bagni", 0))
    row("Bagni da ristrutturare", "Si" if data.get("rifare_bagni") else "No")
    row("Costo bagni", f"{risultati['costo_bagni']:,.0f} euro")

    row("Numero finestre", data.get("finestre", 0))
    row("Finestre da sostituire", "Si" if data.get("rifare_finestre") else "No")
    row("Costo finestre", f"{risultati['costo_finestre']:,.0f} euro")

    row("Numero portefinestre", data.get("portefinestre", 0))
    row("Portefinestre da sostituire", "Si" if data.get("rifare_portefinestre") else "No")
    row("Costo portefinestre", f"{risultati['costo_portefinestre']:,.0f} euro")

    row("Rifacimento impianto elettrico", "Si" if data.get("rifare_impianto") else "No")
    row("Costo impianto elettrico", f"{risultati['costo_impianto']:,.0f} euro")

    row("Rifacimento pavimenti", "Si" if data.get("rifare_pavimenti") else "No")
    row("Costo pavimenti", f"{risultati['costo_pavimenti']:,.0f} euro")

    row("Tinteggio completo appartamento", "Si" if data.get("tinteggio") else "No")
    row("Costo tinteggio", f"{risultati['costo_tinteggio']:,.0f} euro")

    row("Budget generico inserito", f"{risultati['budget_generico']:,.0f} euro")
    row("Altri lavori (descrizione)", data.get("extra_descrizione", "Nessuno"))
    row("Costo extra stimato", f"{risultati['extra_importo']:,.0f} euro")

    # TOTALE
    section_title("Totale indicativo ristrutturazione")
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(0, 140, 70)
    pdf.cell(0, 8, f"Totale lavori stimato: {risultati['totale_lavori']:,.0f} euro", ln=1)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    pdf.set_font("Arial", "", 8)
    pdf.multi_cell(
        0,
        4,
        "Il presente preventivo ha valore indicativo per uso interno Seven Houses. "
        "Importi e lavorazioni dovranno essere confermati a seguito di sopralluogo tecnico.",
    )

    pdf.ln(4)
    pdf.set_text_color(*grigio)
    pdf.cell(0, 5, f"Generato il {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1, align="R")

    filename = f"preventivo_{int(datetime.now().timestamp())}.pdf"
    filepath = os.path.join(PDF_DIR, filename)
    pdf.output(filepath)

    return filepath


def invia_email_con_pdf(data, risultati, filepath):
    """Invia il PDF SOLO a Seven Houses (EMAIL_TUA)."""
    with open(filepath, "rb") as f:
        pdf_data = f.read()

    msg = EmailMessage()
    msg["Subject"] = "Nuovo lead preventivo ristrutturazione - Seven Houses"
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_TUA

    msg.set_content(
        "Nuova richiesta di preventivo ristrutturazione.\n\n"
        f"Nome: {data.get('nome','')} {data.get('cognome','')}\n"
        f"Email cliente: {data.get('email','')}\n"
        f"Telefono: {data.get('telefono','')}\n"
        f"Zona: {data.get('zona','')} - Indirizzo: {data.get('indirizzo','')}\n"
        f"Metri quadri: {data.get('mq',0)}\n\n"
        f"Totale lavori stimato: {risultati['totale_lavori']:,.0f} euro\n\n"
        "Vedi allegato per il dettaglio completo."
    )

    msg.add_attachment(
        pdf_data,
        maintype="application",
        subtype="pdf",
        filename=os.path.basename(filepath),
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Dati cliente
        nome = request.form.get("nome", "").strip()
        cognome = request.form.get("cognome", "").strip()
        email = request.form.get("email", "").strip()
        telefono = request.form.get("telefono", "").strip()

        # Dati immobile
        zona = request.form.get("zona", "").strip()
        indirizzo = request.form.get("indirizzo", "").strip()
        mq = float(request.form.get("mq", 0) or 0)

        # Lavori
        budget_generico = float(request.form.get("budget_generico", 0) or 0)
        bagni = int(request.form.get("bagni", 0) or 0)
        rifare_bagni = bool(request.form.get("rifare_bagni"))
        finestre = int(request.form.get("finestre", 0) or 0)
        rifare_finestre = bool(request.form.get("rifare_finestre"))
        portefinestre = int(request.form.get("portefinestre", 0) or 0)
        rifare_portefinestre = bool(request.form.get("rifare_portefinestre"))
        rifare_impianto = bool(request.form.get("rifare_impianto"))
        rifare_pavimenti = bool(request.form.get("rifare_pavimenti"))
        tinteggio = bool(request.form.get("tinteggio"))
        extra_descrizione = request.form.get("extra_descrizione", "").strip()
        extra_importo = float(request.form.get("extra_importo", 0) or 0)

        data = {
            "nome": nome,
            "cognome": cognome,
            "email": email,
            "telefono": telefono,
            "zona": zona,
            "indirizzo": indirizzo,
            "mq": mq,
            "budget_generico": budget_generico,
            "bagni": bagni,
            "rifare_bagni": rifare_bagni,
            "finestre": finestre,
            "rifare_finestre": rifare_finestre,
            "portefinestre": portefinestre,
            "rifare_portefinestre": rifare_portefinestre,
            "rifare_impianto": rifare_impianto,
            "rifare_pavimenti": rifare_pavimenti,
            "tinteggio": tinteggio,
            "extra_descrizione": extra_descrizione,
            "extra_importo": extra_importo,
        }

        risultati = calcola_preventivo(data)
        pdf_path = genera_pdf_preventivo(data, risultati)

        try:
            invia_email_con_pdf(data, risultati, pdf_path)
        except Exception as e:
            print("Errore invio email:", e)

        # Il cliente vede solo la pagina di ringraziamento, senza prezzi
        return render_template("thankyou.html", nome=nome)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
