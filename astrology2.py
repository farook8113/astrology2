from flask import Flask, request, render_template_string, redirect, url_for
from datetime import datetime
import random
import hashlib

app = Flask(__name__)

BASE_HTML = """
<!doctype html>
<html lang="ml">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>AstroPredict Malayalam — Past, Present & Future</title>
  <style>
    :root{--bg:#0f1724;--card:#0b1220;--muted:#9aa4b2;--accent:#7c3aed}
    body{font-family:Inter,system-ui,Segoe UI,Roboto,Arial, Noto Sans Malayalam, 'Malayalam MN', 'Kartika';margin:0;background:linear-gradient(180deg,#071129,#071f2b);color:white}
    .container{max-width:920px;margin:24px auto;padding:20px}
    .card{background:rgba(255,255,255,0.03);padding:22px;border-radius:12px;box-shadow:0 6px 30px rgba(2,6,23,0.6)}
    h1{margin:0 0 12px;font-size:1.6rem}
    label{display:block;margin-top:12px;color:var(--muted);font-size:0.95rem}
    input,select,textarea{width:100%;padding:10px;margin-top:6px;border-radius:8px;background:transparent;border:1px solid rgba(255,255,255,0.06);color:white}
    .row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
    .btn{display:inline-block;padding:10px 16px;border-radius:10px;background:linear-gradient(90deg,var(--accent),#3b82f6);border:none;color:white;font-weight:600;margin-top:12px}
    .meta{font-size:0.85rem;color:var(--muted);margin-top:8px}
    .result{margin-top:18px;padding:16px;border-radius:10px;background:linear-gradient(180deg,rgba(255,255,255,0.02),rgba(255,255,255,0.01));color:#e6eef8}
    .section{margin-top:10px}
    .section h3{margin:6px 0}
    footer{margin-top:18px;color:var(--muted);font-size:0.85rem;text-align:center}
    @media (max-width:760px){.row{grid-template-columns:1fr}}
  </style>
</head>
<body>
  <div class="container">
    <div class="card">
      <h1>AstroPredict — മികച്ച വിശദാംശങ്ങൾ (മലയാളം)</h1>
      <p class="meta">പേര്, ജനനതിയ്യതി, സമയം (ഐച്ഛികം), ജനനസ്ഥലം നൽകുക — ഭാഷയായി മലയാളം തിരഞ്ഞെടുക്കുക, വിശദത കൂടുതലാക്കാൻ "Detailed" തിരഞ്ഞെടുക്കുക.</p>
      <form method="post" action="{{ url_for('predict') }}">
        <label>പേര്</label>
        <input name="name" required placeholder="പൂർണ്ണനാമം">

        <div class="row">
          <div>
            <label>ജനനതിയ്യതി</label>
            <input type="date" name="dob" required>
          </div>
          <div>
            <label>ജനനസമയം (ഐച്ഛികം)</label>
            <input type="time" name="time">
          </div>
        </div>

        <label>ജനനസ്ഥലം (നഗരം / രാജ്യം)</label>
        <input name="place" placeholder="eg: Kochi, India">

        <label>ഭാഷ</label>
        <select name="lang">
          <option value="ml">മലയാളം</option>
          <option value="en">English</option>
        </select>

        <label>വിവരനിരപ്പ്</label>
        <select name="level">
          <option value="detailed">Detailed (വ്യാപകമായ)</option>
          <option value="short">Short (സംക്ഷിപ്തം)</option>
        </select>

        <button class="btn" type="submit">Prediction ഉണ്ടാക്കുക</button>
      </form>

      {% if prediction %}
      <div class="result">
        <div><strong>{{ prediction['heading'] }}</strong></div>
        <div class="section"><strong>സൺ സൈൻ:</strong> {{ prediction['sun_sign'] }} — {{ prediction['sun_line'] }}</div>

        <div class="section"><h3>കഴിഞ്ഞകാലം (Past)</h3><p>{{ prediction['past'] }}</p></div>
        <div class="section"><h3>നിലവാരം (Present)</h3><p>{{ prediction['present'] }}</p></div>
        <div class="section"><h3>ഭാവി (Future)</h3><p>{{ prediction['future'] }}</p></div>

        <div class="section"><h3>വിവാഹജീവിതം (Marriage)</h3><p>{{ prediction['marriage'] }}</p></div>
        <div class="section"><h3>വ്യവസായ / ബിസിനസ് (Business)</h3><p>{{ prediction['business'] }}</p></div>
        <div class="section"><h3>ധനം & സാമ്പത്തികം (Wealth & Finance)</h3><p>{{ prediction['wealth'] }}</p></div>
        <div class="section"><h3>ആരോഗ്യം (Health)</h3><p>{{ prediction['health'] }}</p></div>
        <div class="section"><h3>വ്യക്തിത്വം & ഉപദേശം (Personality & Advice)</h3><p>{{ prediction['advice'] }}</p></div>

      </div>
      {% endif %}

      <footer>AstroPredict — Malayalam detailed generator. Customize templates in the code for tone and length.</footer>
    </div>
  </div>
</body>
</html>
"""

SUN_SIGNS = [
    (120, "മകരം (Capricorn)"), (218, "കുംബം (Aquarius)"), (320, "മീനം (Pisces)"), (420, "മേടം (Aries)"),
    (521, "വൃശ്ചികം (Taurus)"), (621, "മിഥുനം (Gemini)"), (723, "കരകം (Cancer)"), (823, "സിംഹം (Leo)"),
    (923, "കന്നി (Virgo)"), (1023, "തുലാ (Libra)"), (1122, "ವೃಶ್ಚികം (Scorpio)"), (1222, "ധനുസ്സ് (Sagittarius)"),
]

# Rich Malayalam templates covering all required sections
TEMPLATES = {
    'ml':{
        'heading':'{name} — ജനനതിയ്യതി {dob} സമയം {time} ജനനസ്ഥലം {place}',
        'sun_line':{
            'മകരം (Capricorn)':'പ്രായോഗികത, ഉത്തരവാദിത്വം, ദീര്‍ഘകാല ലക്ഷ്യസാധനം.',
            'കുംബം (Aquarius)':'വിപ്ലവാത്മക ചിന്ത, സമൂഹാനുകൂല സമീപനം, നൂതനത.',

            'മീനം (Pisces)':'ഭാവനാശക്തി, സഹാനുഭൂതി, ആന്തരിക ബുദ്ധിമുട്ടുകൾക്കും ദ്വന്ദ്വങ്ങള്‍ക്കും സെൻസിറ്റിവിറ്റി.',
            'മേടം (Aries)':'ധീരതയും പ്രേരണയും, മുന്നോട്ട് നിൽക്കാനുള്ള ശേഷി.',
            'വൃശ്ചികം (Taurus)':'സ്ഥിരത, ആസക്തി, വസ്തുനിഷ്ഠത.',
            'മിഥുനം (Gemini)':'കൗതുകം, ആശയവിനിമയം, മടക്കം ഇല്ലാത്ത മനോഭാവം.',
            'കരകം (Cancer)':'പരിപാലനം, കുടുംബമേഖലയിൽ ശക്തി, വികാരപരത.',
            'സിംഹം (Leo)':'ആത്മവിശ്വാസം, സൃഷ്ടിപരത, നേതൃത്വബോധം.',
            'കന്നി (Virgo)':'വിശകലനം, സൗകര്യപ്രധാനമായ സേവനം, ലളിതത്വം.',
            'തുലാ (Libra)':'സമതുലിതത്വം, സൗന്ദര്യബോധം, ബന്ധനിർമിതി.',
            'ವೃಶ್ಚികം (Scorpio)':'ഗൗരവം, പരിവര്‍ത്തനശക്തി, അന്വേഷണ സൂക്ഷ്മത.',
            'ധനുസ്സ് (Sagittarius)':'സ്വതന്ത്രത, ദര്‍ശനപരമായ ആഗ്രഹം, യാത്രാമനോഭാവം.'
        },
        'past_templates':[
            "കഴിഞ്ഞ കാലത്ത്, ജീവിതത്തിൽ നിങ്ങൾ ശക്തമായ പാഠങ്ങൾ പഠിച്ചു. കുടുംബജീവിതത്തിൽ, വിദ്യാഭ്യാസത്തിൽ അല്ലെങ്കിൽ തൊഴിൽപരമായവയിൽ നിന്ന് നിങ്ങൾക്കുണ്ടായ അനുഭവങ്ങൾ ഇപ്പോഴത്തെ നിലയിൽ വലിയ സ്വാധീനം ചെലുത്തിയിരിക്കുന്നു.",
            "മുൻകാലത്തിലെ ഉയർച്ചകളും ഇടിവുകളും നിങ്ങൾക്ക് ചുമതലമേറ്റ ശീലങ്ങളും സമീപനങ്ങളും കൊടുത്തു. ചില സമയങ്ങളിൽ സാമ്പത്തിക പ്രതിസന്ധികൾ ഉണ്ടായിട്ടുണ്ടെങ്കിലും, അവ നിങ്ങളുടെ കൈവശം നിക്ഷേപം/സംഘടനാ കഴിവ് വർദ്ധിപ്പിച്ചതായി കാണാം."
        ],
        'present_templates':[
            "നിലവിൽ, നിങ്ങൾ ഒരു മണ്ഡലത്തിൽ ശ്രദ്ധ കേന്ദ്രീകരിച്ചിരിക്കുകയാണ് — ഇത് ജോലി, റൊമാന്റിക് ബന്ധം, അല്ലെങ്കിൽ വ്യക്തിഗത വളർച്ച ആകാം. ഈ ഘട്ടത്തിൽ തീർച്ചയായും ആത്മവിശ്വാസവും പ്രവർത്തനക്ഷമതയും ആവശ്യമാണ്.",
            "ഇപ്പോൾ നിങ്ങളുടെ ഊർജ്ജത്തിന്റെ പ്രധാന ദിശ ബന്ധങ്ങൾക്കും സാമ്പത്തിക കാര്യങ്ങൾക്കും സർക്കുലാറ്റ് ചെയ്യുകയാണ്. സംവേദനശീലവും കുറ്റമറ്റ ആശയവിനിമയവും ഇന്ന് സഹായകമാണ്."
        ],
        'future_templates':[
            "ഭാവിയിൽ അടുത്ത 6–18 മാസംക്കുള്ളിൽ സാധാരണയായി ഒരു പുതിയ അവസരം പ്രതീക്ഷിക്കാം — ജോലി, ഊർജ്ജപരിഷ്കാരം, അല്ലെങ്കിൽ ബന്ധത്തിന്റെ ഉന്നതിവേവ്. ഇത് നിർബന്ധമായും പ്രവർത്തനവും ബുദ്ധിമുട്ടും ആവശ്യപ്പെടും, പക്ഷേ ഇത് വളർച്ചക്കും എളുപ്പവും നൽകും.",
            "നിങ്ങളുടെ സാമ്പത്തിക സ്ഥിതി ക്രമീകരിക്കാൻ നല്ല അവസരങ്ങൾ മുന്നിലേക്ക് വരാൻ സാധ്യതയുണ്ട്. സ്ഥിരതയുള്ള നിക്ഷേപവും ജാഗ്രതയുള്ള ചെലവഴിക്കലും ഇത് പിന്തുണക്കും."
        ],
        'marriage_templates':[
            "വിവാഹ ജീവിതത്തിൽ ബന്ധത്തിന്റെ ആശയവിനിമയം വളരെ പ്രധാനമാണ്. ഒരുമിച്ചിരിക്കുമ്പോൾ തുറന്നു സംസാരിക്കുക, ഭാവിതലങ്ങളുമായി ബന്ധപ്പെട്ട പ്രതീക്ഷകൾ വ്യക്തമാക്കുക.",
            "വിവാഹം അല്ലെങ്കിൽ നിർണ്ണായക ബന്ധങ്ങൾ ശക്തിപ്പെടാൻ അടിയന്തരമായി ആത്മസംയമവും സഹനവും ആവശ്യമാണ്. വിചാരണകൾ വരുമ്പോൾ ക്ഷമയാണ് കൂടുതൽ ഫലപ്രദമാകുന്നത്."
        ],
        'business_templates':[
            "ബിസിനസിൽ മാറ്റങ്ങൾക്ക് തയ്യാറെടുക്കുക — പുതിയ ആശയങ്ങൾ പരീക്ഷിക്കാൻ സന്നദ്ധരാകുക. കൂട്ടായ്മകളും പങ്കാളിത്തങ്ങളും നിങ്ങളുടെ വിജയത്തിൽ സുപ്രധാനമായി മാറും.",
            "വിപണിയിലെ മാറ്റങ്ങൾ നിരീക്ഷിക്കുക; പഴയ രീതികളിലേക്കു മാത്രം ആശ്രയിക്കരുത്. മിതമായ റിസ്ക് അടിമുടി ചെയ്യുമ്പോൾ ഉയർച്ച ഒന്നുകിൽ വരാം."
        ],
        'wealth_templates':[
            "സാമ്പത്തിക കാര്യത്തിൽ, വരുമാന സ്രോതസ്സുകൾ വൈവിധ്യമാക്കുക. ആനാവശ്യമായ ചില ചെലവുകൾ കുറച്ചുചേര്‍ക്കുകയും ദീർഘാഭിപ്രായക്കായി നിക്ഷേപങ്ങൾ നൽകുകയും ചെയ്യുക.",
            "വളരെ പൊതു ഉപദേശം: വലിയ സാമ്പത്തിക തീരുമാനം എടുക്കുമ്പോൾ സംവെധാനവും, കരുതലും ആദ്യം പ്രവർത്തിപ്പിക്കുക. പ്രതീക്ഷിത ചെലവുകൾക്കായി സേവിംഗ്സ് ക്രമീകരിക്കുക."
        ],
        'health_templates':[
            "ആരോഗ്യം സംബന്ധിച്ച കാര്യങ്ങൾ സ്ഥിരതയോടെ നിയന്ത്രിക്കുക— വിശ്രമം, ശരിയായ ഭക്ഷണക്രമം, ലഘു വ്യായാമം എന്നിവ പ്രധാനമാണ്.",
            "മനസിക സമ്മർദം കൃത്യമായി കൈകാര്യം ചെയ്യാൻ യോഗം / മെഡിറ്റേഷൻ പോലുള്ള അഭ്യാസങ്ങൾ സഹായകമാണ്. ചെറിയ അസ്വാസ്ഥ്യങ്ങളെത്തുമ്പോൾ ഡോക്ടറിന്റെ ഉപദേശം തേടുക."
        ],
        'advice_templates':[
            "നിങ്ങളുടെ ഊർജ്ജം നിയന്ത്രിച്ച് പ്രധാന ലക്ഷ്യങ്ങളിലേക്കു ശ്രദ്ധ കേന്ദ്രീകരിക്കുക. നിത്യജീവിതത്തിലെ ചെറിയ ചവിട്ടുകള്‍ വലിയ വ്യത്യാസം സൃഷ്ടിക്കും.",
            "സൗഹൃദങ്ങളും കുടുംബബന്ധങ്ങളും കൂടുതൽ ശ്രദ്ധിക്കൂ; അവ നിങ്ങളുടെ ആത്മിക-സാമ്പത്തിക പിന്തുണയിൽ സഹായിക്കും."
        ]
    },
    'en':{
        'heading':'{name} — born on {dob} at {time} in {place}',
        'sun_line':{},
        'past_templates':['In the past, you learned key lessons that shaped your values and resilience.'],
        'present_templates':['Currently you are focusing on growth areas; communication and discipline will help you achieve goals.'],
        'future_templates':['Expect changes that bring opportunities in the coming months; prepare and be flexible.'],
        'marriage_templates':['Marriage and partnerships will require honest communication and compromise to thrive.'],
        'business_templates':['Be open to innovation and partnerships; moderate risk can bring significant rewards.'],
        'wealth_templates':['Diversify income streams and save for irregular expenses; plan before major investments.'],
        'health_templates':['Prioritize sleep, balanced diet, and moderate exercise; mental health practices will help.'],
        'advice_templates':['Focus on consistent small improvements and nurture close relationships.']
    }
}


def compact_date_key(dt: datetime):
    return dt.month * 100 + dt.day


def sun_sign_from_date(dob_dt: datetime):
    key = compact_date_key(dob_dt)
    for cutoff, sign in SUN_SIGNS:
        if key <= cutoff:
            return sign
    return SUN_SIGNS[0][1]


def deterministic_random_seed(*parts):
    s = "|".join([str(p) for p in parts])
    h = hashlib.sha256(s.encode('utf-8')).hexdigest()
    return int(h[:16], 16)


def expand_long_paragraphs(rng, templates, slots_count=3):
    # pick several templates and join with variations to create a long detailed paragraph
    parts = []
    for _ in range(slots_count):
        t = rng.choice(templates)
        parts.append(t)
    # add some deterministic detail sentences
    details = [
        "ഈ ഘട്ടത്തിൽ നിജമായ തീരുമാനങ്ങൾ വേണമെന്നും, നിർണ്ണായകമായ തീരുമാനങ്ങൾ എടുക്കുമ്പോൾ നിങ്ങളുടെ ശ്രദ്ധാകേന്ദ്രങ്ങൾ ക്രമീകരിക്കേണ്ടതുണ്ടെന്ന് കാണാം.",
        "പറയാനുണ്ടായ ഒരു കാര്യം: നേരത്തെ ഉണ്ടായ കണ്ടെത്തലുകൾ ഈ സാഹചര്യത്തിൽ പുതിയ അവസരങ്ങൾ സൃഷ്ടിക്കാനും സഹായിക്കും.",
        "നിങ്ങളുടെ സാമൂഹിക ബന്ധങ്ങൾ അടുത്ത കാലത്ത് കൂടുതൽ പ്രാധാന്യമാകാൻ സാധ്യതയുണ്ട്; അവയിൽ നിക്ഷേപം നടത്തുക."
    ]
    parts.append(rng.choice(details))
    return ' '.join(parts)


def build_prediction(name, dob_str, time_str, place, lang, level):
    tpl = TEMPLATES.get(lang, TEMPLATES['en'])
    dob_dt = datetime.strptime(dob_str, "%Y-%m-%d")
    sun = sun_sign_from_date(dob_dt)

    seed = deterministic_random_seed(name.lower(), dob_str, time_str or '', place or '')
    rng = random.Random(seed)

    # Build long Malayalam paragraphs when level == 'detailed' and lang == 'ml'
    if lang == 'ml' and level == 'detailed':
        past = expand_long_paragraphs(rng, tpl['past_templates'], slots_count=3)
        present = expand_long_paragraphs(rng, tpl['present_templates'], slots_count=3)
        future = expand_long_paragraphs(rng, tpl['future_templates'], slots_count=3)
        marriage = expand_long_paragraphs(rng, tpl['marriage_templates'], slots_count=3)
        business = expand_long_paragraphs(rng, tpl['business_templates'], slots_count=3)
        wealth = expand_long_paragraphs(rng, tpl['wealth_templates'], slots_count=3)
        health = expand_long_paragraphs(rng, tpl['health_templates'], slots_count=3)
        advice = expand_long_paragraphs(rng, tpl['advice_templates'], slots_count=3)
    else:
        # short or English: pick single templates
        past = rng.choice(tpl['past_templates'])
        present = rng.choice(tpl['present_templates'])
        future = rng.choice(tpl['future_templates'])
        marriage = rng.choice(tpl['marriage_templates'])
        business = rng.choice(tpl['business_templates'])
        wealth = rng.choice(tpl['wealth_templates'])
        health = rng.choice(tpl['health_templates'])
        advice = rng.choice(tpl['advice_templates'])

    heading = tpl['heading'].format(name=name, dob=dob_str, time=time_str or 'Unknown', place=place or 'Unknown')
    sun_line = tpl['sun_line'].get(sun, '')

    # Add a few personalized deterministic sentences to each section
    def add_personal_note(text, rng_obj):
        note_templates_ml = [
            "നിങ്ങളുടെ ജനനവാർഷികങ്ങൾ കുടുംബപരമായ ഉത്തരവാദിത്വങ്ങൾ ശക്തിപ്പെടുത്തിയ olabilir.",
            "ഈ സന്ദർഭത്തിൽ ധൈര്യത്തോടെ പുതിയ സംരംഭങ്ങളിൽ ചുവടേക്ക് വന്നാൽ നല്ല ഫലം ലഭിക്കാം."
        ]
        if lang == 'ml':
            if rng_obj.randint(0,1):
                return text + ' ' + rng_obj.choice(note_templates_ml)
        return text

    past = add_personal_note(past, rng)
    present = add_personal_note(present, rng)
    future = add_personal_note(future, rng)
    marriage = add_personal_note(marriage, rng)
    business = add_personal_note(business, rng)
    wealth = add_personal_note(wealth, rng)
    health = add_personal_note(health, rng)
    advice = add_personal_note(advice, rng)

    return {
        'heading': heading,
        'sun_sign': sun,
        'sun_line': sun_line,
        'past': past,
        'present': present,
        'future': future,
        'marriage': marriage,
        'business': business,
        'wealth': wealth,
        'health': health,
        'advice': advice
    }


@app.route('/', methods=['GET'])
def index():
    return render_template_string(BASE_HTML, prediction=None)


@app.route('/predict', methods=['POST'])
def predict():
    name = request.form.get('name', 'Unknown')
    dob = request.form.get('dob')
    time = request.form.get('time')
    place = request.form.get('place')
    lang = request.form.get('lang', 'ml')
    level = request.form.get('level', 'detailed')

    if not dob:
        return redirect(url_for('index'))

    prediction = build_prediction(name, dob, time, place, lang, level)
    return render_template_string(BASE_HTML, prediction=prediction)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
