from flask import Flask, request, render_template_string, redirect, url_for, flash
from decimal import Decimal, InvalidOperation
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import RawBtIntents

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me-in-production")

HTML_PAGE = """
<!doctype html>
<html lang="pl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>RawBT Print</title>
  <style>
    :root { --bg:#f7f7f9; --card:#fff; --border:#ddd; --primary:#1f6feb; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 24px;
      background: var(--bg);
      font-family: Arial, sans-serif;
      color: #111;
    }
    .wrap {
      max-width: 560px;
      margin: 0 auto;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
    }
    h2 { margin-top: 0; }
    .row { margin-bottom: 14px; }
    .label { display:block; font-weight: 600; margin-bottom: 8px; }
    .radio-group {
      display: flex;
      gap: 18px;
      align-items: center;
    }
    input[type="text"] {
      width: 100%;
      padding: 10px 12px;
      border: 1px solid var(--border);
      border-radius: 8px;
      font-size: 16px;
    }
    .hint { font-size: 13px; color: #666; margin-top: 6px; }
    button {
      width: 100%;
      padding: 11px 14px;
      border: 0;
      border-radius: 10px;
      background: var(--primary);
      color: #fff;
      font-size: 16px;
      cursor: pointer;
    }
    button:hover { opacity: 0.95; }
    .msg {
      margin-bottom: 12px;
      padding: 10px 12px;
      border-radius: 8px;
      background: #fff4e5;
      border: 1px solid #ffd59e;
      color: #8a4b00;
    }
  </style>
</head>
<body>
  <div class="wrap">
    <h2>RawBT Printer</h2>

    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for m in messages %}
          <div class="msg">{{ m }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <form method="post" action="{{ url_for('do_print') }}">
      <div class="row">
        <span class="label">Wybór</span>
        <div class="radio-group">
          <label><input type="radio" name="mode" value="BET" checked> BET</label>
          <label><input type="radio" name="mode" value="OUT"> OUT</label>
        </div>
      </div>

      <div class="row">
        <label class="label" for="amount">Kwota</label>
        <input
          id="amount"
          name="amount"
          type="text"
          inputmode="decimal"
          placeholder="np. 100"
          required
        >
        <div class="hint">Wpisz samą liczbę (np. 100 lub 100,50) — system dopisze „zł”.</div>
      </div>

      <button type="submit">Print</button>
    </form>
  </div>
</body>
</html>
"""


def parse_amount(raw: str) -> str:
    """
    Parsuje i normalizuje kwotę:
    - akceptuje przecinek i kropkę,
    - usuwa spacje,
    - zwraca format PL: 100 lub 100,50
    """
    if raw is None:
        raise ValueError("Brak kwoty")

    cleaned = raw.strip().replace(" ", "").replace(",", ".")
    if cleaned == "":
        raise ValueError("Kwota nie może być pusta")

    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        raise ValueError("Nieprawidłowa kwota")

    if value < 0:
        raise ValueError("Kwota nie może być ujemna")

    quantized = value.quantize(Decimal("0.01"))
    if quantized == quantized.to_integral():
        pl = f"{int(quantized)}"
    else:
        pl = format(quantized, "f").replace(".", ",")
    return pl


@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_PAGE)


@app.route("/print", methods=["POST"])
def do_print():
    mode = (request.form.get("mode") or "").upper()
    raw_amount = request.form.get("amount", "")

    if mode not in {"BET", "OUT"}:
        flash("Nieprawidłowy wybór. Wybierz BET lub OUT.")
        return redirect(url_for("index"))

    try:
        amount_pl = parse_amount(raw_amount)
    except ValueError as e:
        flash(str(e))
        return redirect(url_for("index"))

    # NOWA LINIA: data/czas
    date_line = datetime.now(ZoneInfo("Europe/Warsaw")).strftime("%d.%m.%Y %H:%M")

    # Wydruk: 1) BET/OUT 2) kwota 3) data
    text_to_print = f"IgoCheap\nCasino printer\n\n{mode}\n{amount_pl} zł\n{date_line}\nNo refunds.\n\n"

    intent_uri = RawBtIntents.print_text(text_to_print)
    return redirect(intent_uri, code=302)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
