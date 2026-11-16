"""Tests de fumée de Closer (navigateur réel, sans réseau : Supabase est simulé).
Lancer depuis la racine du dépôt :  python3 -m http.server 8766 &  puis  python3 tests/smoke.py
Nécessite : pip install playwright  (et un Chrome/Chromium)."""
import json, os, sys, itertools
from playwright.sync_api import sync_playwright

URL = os.environ.get('CLOSER_URL', 'http://localhost:8766/index.html')
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome')
LAUNCH = {'args': ['--no-sandbox']}
if CHROME and os.path.exists(CHROME):
    LAUNCH['executable_path'] = CHROME
SB = 'https://test.supabase.co'
CFG = {'url': SB, 'key': 'sb_publishable_test', 'contact': 'test@exemple.fr'}

# --- faux Supabase, partagé par tous les « appareils » du test ---
MOCK_JS = r"""
export function createClient(){
  const cbs=[]; const call=(op,a)=>window.__srv(op,JSON.stringify(a)).then(r=>JSON.parse(r));
  const cur=()=>{const s=JSON.parse(localStorage.getItem('mock-sess')||'null');return s&&s.user.id;};
  const auth={
    getSession:async()=>({data:{session:JSON.parse(localStorage.getItem('mock-sess')||'null')}}),
    onAuthStateChange(f){cbs.push(f);return {data:{subscription:{unsubscribe(){}}}};},
    async signInWithPassword(a){const r=await call('login',a);if(r.error)return r;const s={user:r.user};localStorage.setItem('mock-sess',JSON.stringify(s));setTimeout(()=>cbs.forEach(f=>f('SIGNED_IN',s)));return {error:null};},
    async signUp(a){return call('signup',a);},
    async signOut(){localStorage.removeItem('mock-sess');cbs.forEach(f=>f('SIGNED_OUT',null));return {error:null};},
    async resetPasswordForEmail(){return {error:null};}, async resend(){return {error:null};}, async updateUser(){return {error:null};}
  };
  function from(){const q={};const b={select(){return b;},gt(c,v){q.gt=v;return b;},order(){return b;},
    range(a,z){q.range=[a,z];q.uid=cur();return call('select',q);},
    upsert(rows){return call('upsert',{rows,uid:cur()});}};return b;}
  return {auth,from,rpc:async(n)=>call('rpc',{n,uid:cur()})};
}
"""
USERS, ROWS, EVENTS = {}, {}, []
CLOCK = itertools.count(1_700_000_000_000, 1000)

def srv(op, raw):
    a = json.loads(raw)
    if op == 'signup':
        if a['email'] in USERS:
            return json.dumps({'data': {'user': {'identities': []}, 'session': None}, 'error': None})
        USERS[a['email']] = {'pw': a['password'], 'id': 'u-' + str(len(USERS) + 1), 'conf': True}
        return json.dumps({'data': {'user': {'identities': [{}]}, 'session': None}, 'error': None})
    if op == 'login':
        u = USERS.get(a['email'])
        if not u or u['pw'] != a['password']:
            return json.dumps({'error': {'message': 'Invalid login credentials'}})
        return json.dumps({'user': {'id': u['id'], 'email': a['email']}})
    if op == 'select':
        rows = sorted((r for (uid, _), r in ROWS.items() if uid == a['uid'] and r['updated_at'] > a.get('gt', 0)), key=lambda r: r['updated_at'])
        z0, z1 = a['range']
        return json.dumps({'data': rows[z0:z1 + 1], 'error': None})
    if op == 'upsert':
        for r in a['rows']:
            assert r['user_id'] == a['uid'], 'écriture pour un autre utilisateur'
            ROWS[(a['uid'], r['id'])] = {'id': r['id'], 'data': r['data'], 'deleted': r['deleted'], 'updated_at': next(CLOCK)}
        return json.dumps({'error': None})
    if op == 'rpc':
        for k in [k for k in ROWS if k[0] == a['uid']]:
            del ROWS[k]
        for e, u in list(USERS.items()):
            if u['id'] == a['uid']:
                del USERS[e]
        return json.dumps({'error': None})
    return json.dumps({'error': {'message': 'op inconnue'}})

ok = True
def check(name, cond):
    global ok
    print(('OK   ' if cond else 'ÉCHEC'), name)
    ok = ok and bool(cond)

with sync_playwright() as p:
    b = p.chromium.launch(**LAUNCH)

    def device(cfg=True, appv_online=None):
        c = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, locale='fr-FR', timezone_id='Europe/Paris')
        c.route('https://fonts.googleapis.com/**', lambda r: r.abort())
        c.route('https://fonts.gstatic.com/**', lambda r: r.abort())
        c.route('https://cdn.jsdelivr.net/**', lambda r: r.fulfill(status=200, content_type='application/javascript', body=MOCK_JS))
        c.route(SB + '/rest/v1/closer_events', lambda r: (EVENTS.extend(json.loads(r.request.post_data or '[]')), r.fulfill(status=201, body='')))
        if appv_online:
            def page_route(r):
                if '?v=' in r.request.url:
                    resp = r.fetch()
                    body = resp.text().replace('var APPV="', 'var APPV="' + appv_online + '-', 1)
                    r.fulfill(status=200, content_type='text/html', body=body)
                else:
                    r.continue_()
            c.route('**/index.html*', page_route)
        c.expose_function('__srv', srv)
        c.add_init_script('window.__CLOSER_TEST=1;window.__CLOSER_CFG=' + json.dumps(CFG if cfg else {'url': '', 'key': ''}) + ';')
        pg = c.new_page()
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(URL)
        pg.wait_for_timeout(700)
        return c, pg, errs

    def add_task(pg, title):
        pg.click('#fab')
        pg.wait_for_timeout(250)
        pg.fill('#sh-title', title)
        pg.press('#sh-title', 'Enter')
        pg.wait_for_timeout(250)

    def items(pg):
        return pg.evaluate("JSON.parse(localStorage.getItem('cap-items-v1')||'[]').filter(e=>e[1].kind!=='prefs').map(e=>e[1].title).sort()")

    def open_account(pg):
        pg.click('#ac-btn')
        pg.wait_for_timeout(250)

    def login(pg, email, pw):
        open_account(pg)
        pg.fill('#ac-em', email)
        pg.fill('#ac-pw', pw)
        pg.press('#ac-pw', 'Enter')
        pg.wait_for_timeout(900)

    # 1. Sans réglage Supabase : l'app marche, sans bouton Compte
    c, pg, errs = device(cfg=False)
    add_task(pg, 'Tâche locale')
    pg.reload(); pg.wait_for_timeout(500)
    check('sans compte : la tâche reste après rechargement', items(pg) == ['Tâche locale'])
    check('sans réglage : bouton Compte masqué', pg.is_hidden('#ac-btn'))
    check('sans réglage : aucune erreur', not errs)
    c.close()

    # 2. Appareil A : des tâches locales, création de compte, connexion -> envoi
    a, pa, ea = device()
    add_task(pa, 'Réviser la compta')
    add_task(pa, 'Appeler le banquier')
    check('bouton Compte visible', pa.is_visible('#ac-btn'))
    check('statistique « open » envoyée une fois', [e['ev'] for e in EVENTS].count('open') == 1)
    check('statistique « first_item » envoyée', 'first_item' in [e['ev'] for e in EVENTS])
    open_account(pa)
    pa.click('[data-act="ac-tosignup"]')
    pa.fill('#ac-em', 'max@test.fr'); pa.fill('#ac-pw', 'faible')
    pa.press('#ac-pw', 'Enter'); pa.wait_for_timeout(200)
    check('mot de passe faible refusé', 'trop faible' in pa.inner_text('#sheet'))
    pa.fill('#ac-pw', 'Solide123'); pa.press('#ac-pw', 'Enter'); pa.wait_for_timeout(400)
    check('compte créé, message de confirmation', 'Compte créé' in pa.inner_text('#sheet'))
    pa.fill('#ac-pw', 'Solide123'); pa.press('#ac-pw', 'Enter'); pa.wait_for_timeout(1200)
    check('connecté', 'Connecté' in pa.inner_text('#sheet'))
    srv_titles = sorted(r['data']['title'] for (u, _), r in ROWS.items() if r['data'] and r['data'].get('kind') != 'prefs')
    check('les 2 tâches locales sont sur le compte', srv_titles == ['Appeler le banquier', 'Réviser la compta'])
    check('pastille verte sur Compte', 'ok' in pa.get_attribute('#ac-dot', 'class'))
    pa.click('#sheet [data-act="close-sheet"]')

    # 3. Appareil B (neuf) : connexion -> récupère tout ; modifie et supprime
    bb, pb, eb = device()
    login(pb, 'max@test.fr', 'Solide123')
    check('appareil B : tâches récupérées', items(pb) == ['Appeler le banquier', 'Réviser la compta'])
    pb.click('#sheet [data-act="close-sheet"]')
    add_task(pb, 'Préparer l\'oral')
    # supprimer « Appeler le banquier » depuis sa fiche
    pb.evaluate("location.hash='#taches'"); pb.wait_for_timeout(300)
    tid = pb.evaluate("JSON.parse(localStorage.getItem('cap-items-v1')).find(e=>e[1].title==='Appeler le banquier')[0]")
    pb.click('#v-taches [data-act="edit"][data-id="%s"]' % tid); pb.wait_for_timeout(300)
    pb.click('#sheet [data-act="sheet-del"]'); pb.wait_for_timeout(300)
    pb.wait_for_timeout(2200)  # envoi automatique (1,5 s)
    check('appareil B : suppression et ajout envoyés', sorted(r['data']['title'] for (u, _), r in ROWS.items() if not r['deleted'] and r['data'].get('kind') != 'prefs') == ['Préparer l\'oral', 'Réviser la compta'])

    # 4. Retour sur A : la synchro récupère les changements de B
    pa.evaluate("document.dispatchEvent(new Event('visibilitychange'))"); pa.wait_for_timeout(1200)
    check('appareil A : changements de B reçus', items(pa) == ['Préparer l\'oral', 'Réviser la compta'])
    check('aucune erreur sur A et B', not ea and not eb)

    # 5. Déconnexion : les données restent sur l'appareil
    open_account(pb); pb.click('[data-act="ac-out"]'); pb.wait_for_timeout(500)
    check('déconnecté, données gardées', 'Déconnecté' in pb.inner_text('#sheet') and len(items(pb)) == 2)
    pb.click('#sheet [data-act="close-sheet"]')

    # 6. Statistiques désactivables
    n0 = len(EVENTS)
    open_account(pa); pa.click('[data-act="ac-stats"]'); pa.wait_for_timeout(200)
    check('statistiques désactivées', 'désactivées' in pa.inner_text('#sheet'))
    pa.evaluate("localStorage.removeItem('closer-ev-open-day')"); pa.reload(); pa.wait_for_timeout(800)
    check('plus aucun envoi une fois désactivé', len(EVENTS) == n0)

    # 7. Suppression du compte
    open_account(pa); pa.click('[data-act="ac-del"]'); pa.wait_for_timeout(150); pa.click('[data-act="ac-del"]'); pa.wait_for_timeout(600)
    check('compte supprimé, données en ligne effacées', not ROWS and 'Compte supprimé' in pa.inner_text('#sheet'))
    a.close(); bb.close()

    # 7 bis. Geste iOS : glisser la fiche vers le bas la ferme ; un petit glissement lent la laisse ouverte
    c, pg, errs = device(cfg=False)
    cdp = c.new_cdp_session(pg)
    def swipe(y_from, y_to, steps, pause):
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': 200, 'y': y_from}]})
        for i in range(1, steps + 1):
            pg.wait_for_timeout(pause)
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': 200, 'y': y_from + (y_to - y_from) * i / steps}]})
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
        pg.wait_for_timeout(450)
    pg.click('[data-act="backup"]'); pg.wait_for_timeout(450)
    top = pg.evaluate("document.getElementById('sheet').getBoundingClientRect().top")
    swipe(top + 20, top + 60, 10, 40)
    check('petit glissement lent : la fiche reste ouverte', pg.evaluate("document.body.classList.contains('sheet-open')"))
    check('la fiche revient en place', pg.evaluate("getComputedStyle(document.getElementById('sheet')).transform") in ('none', 'matrix(1, 0, 0, 1, 0, 0)'))
    swipe(top + 20, top + 140, 4, 16)
    check('glissement rapide vers le bas : la fiche se ferme', not pg.evaluate("document.body.classList.contains('sheet-open')"))
    check('pas de débordement horizontal sur iPhone', pg.evaluate("document.documentElement.scrollWidth<=window.innerWidth"))
    check('aucune erreur pendant les gestes', not errs)
    c.close()

    # 8. Bandeau de mise à jour quand une nouvelle version est en ligne
    c, pg, errs = device(appv_online='9999')
    pg.wait_for_timeout(3200)
    check('bandeau « Nouvelle version » affiché', pg.is_visible('#upd'))
    c.close()
    b.close()

print('\nTOUT EST OK' if ok else '\nDES TESTS ONT ÉCHOUÉ')
sys.exit(0 if ok else 1)
