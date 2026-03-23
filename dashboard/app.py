import sqlite3
import os
from urllib.parse import urlencode
from flask import Flask, render_template, request, redirect, url_for, flash
from markupsafe import Markup

app = Flask(__name__)
app.secret_key = 'futbot-dashboard-dev'

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'cards_game.db')

RARITIES = ['Common', 'Uncommon', 'Rare']

POSITIONS = ['GK', 'CB', 'LB', 'RB', 'CDM', 'CM', 'CAM', 'LM', 'RM', 'LW', 'RW', 'ST', 'CF']


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn, name):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def get_card_types(conn):
    """Fetch distinct card_type values from DB for datalist suggestions."""
    rows = conn.execute(
        'SELECT DISTINCT card_type FROM cards WHERE card_type IS NOT NULL ORDER BY card_type'
    ).fetchall()
    types = [r[0] for r in rows if r[0]]
    # Always include base types as fallback suggestions
    for default in ('Standard', 'Icon', 'Hero', 'Normal', 'Euro TOTT', 'Copa America TOTT'):
        if default not in types:
            types.append(default)
    return types


# ── Jinja helpers ──────────────────────────────────────────────────────────────

@app.context_processor
def inject_helpers():
    def sort_th(label, field, cur_sort, cur_order, *filter_vals, **extra):
        new_order = 'asc' if (cur_sort == field and cur_order == 'desc') else 'desc'
        params = dict(extra)
        filter_names = ['search', 'rarity', 'club', 'nation', 'league']
        for i, v in enumerate(filter_vals):
            if v:
                params[filter_names[i]] = v
        params['sort']  = field
        params['order'] = new_order
        qs = urlencode(params)
        active = 'active' if cur_sort == field else ''
        arrow  = ''
        if cur_sort == field:
            icon  = 'caret-down-fill' if cur_order == 'desc' else 'caret-up-fill'
            arrow = f'<i class="bi bi-{icon} ms-1"></i>'
        html = (f'<th><a href="?{qs}" class="th-sort {active}">'
                f'{label}{arrow}</a></th>')
        return Markup(html)

    return dict(sort_th=sort_th)


# ═══════════════════════════════════════════════════════════════════════════════
# CARDS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return redirect(url_for('cards'))


@app.route('/cards')
def cards():
    search = request.args.get('search', '').strip()
    rarity = request.args.get('rarity', '')
    club   = request.args.get('club', '')
    nation = request.args.get('nation', '')
    league = request.args.get('league', '')
    sort   = request.args.get('sort', 'overall')
    order  = request.args.get('order', 'desc')

    allowed = {'card_id', 'player_id', 'name', 'overall', 'attack', 'defense', 'speed',
               'card_rarity', 'club', 'nation'}
    if sort not in allowed:
        sort = 'overall'
    order_sql = 'DESC' if order == 'desc' else 'ASC'

    query  = 'SELECT * FROM cards WHERE 1=1'
    params = []
    if search: query += ' AND name LIKE ?';     params.append(f'%{search}%')
    if rarity: query += ' AND card_rarity = ?'; params.append(rarity)
    if club:   query += ' AND club LIKE ?';      params.append(f'%{club}%')
    if nation: query += ' AND nation LIKE ?';    params.append(f'%{nation}%')
    if league: query += ' AND league LIKE ?';    params.append(f'%{league}%')
    query += f' ORDER BY {sort} {order_sql}'

    conn    = get_db()
    rows    = conn.execute(query, params).fetchall()
    clubs   = [r[0] for r in conn.execute('SELECT DISTINCT club   FROM cards ORDER BY club').fetchall()]
    nations = [r[0] for r in conn.execute('SELECT DISTINCT nation FROM cards ORDER BY nation').fetchall()]
    leagues = [r[0] for r in conn.execute('SELECT DISTINCT league FROM cards ORDER BY league').fetchall()]
    conn.close()

    return render_template('cards.html',
        cards=rows, search=search, rarity=rarity, club=club,
        nation=nation, league=league, sort=sort, order=order,
        rarities=RARITIES, clubs=clubs, nations=nations, leagues=leagues,
        total=len(rows))


@app.route('/cards/add', methods=['GET', 'POST'])
def add_card():
    conn = get_db()
    card_types = get_card_types(conn)
    if request.method == 'POST':
        fields = _parse_card_form(request.form)
        error  = _validate_card(fields)
        if error:
            conn.close()
            flash(error, 'error')
            return render_template('add_card.html', card=fields, rarities=RARITIES,
                                   card_types=card_types, positions=POSITIONS)
        conn.execute('''
            INSERT INTO cards (player_id, name, attack, defense, speed, height,
                               club, position, overall, image_path, card_rarity,
                               card_type, league, nation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (fields['player_id'], fields['name'], fields['attack'], fields['defense'],
              fields['speed'], fields['height'], fields['club'], fields['position'],
              fields['overall'], fields['image_path'], fields['card_rarity'],
              fields['card_type'], fields['league'], fields['nation']))
        conn.commit()
        new_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()
        flash(f'Card "{fields["name"]}" added (ID {new_id}).', 'success')
        return redirect(url_for('cards'))

    conn.close()
    return render_template('add_card.html', card={}, rarities=RARITIES,
                           card_types=card_types, positions=POSITIONS)


@app.route('/cards/<int:card_id>', methods=['GET', 'POST'])
def edit_card(card_id):
    conn = get_db()
    card_types = get_card_types(conn)
    if request.method == 'POST':
        fields = _parse_card_form(request.form)
        error  = _validate_card(fields)
        if error:
            flash(error, 'error')
            card = conn.execute('SELECT * FROM cards WHERE card_id = ?', (card_id,)).fetchone()
            conn.close()
            return render_template('edit_card.html', card={**dict(card), **fields},
                                   rarities=RARITIES, card_types=card_types, positions=POSITIONS)
        conn.execute('''
            UPDATE cards SET player_id=?, name=?, attack=?, defense=?, speed=?,
                height=?, club=?, position=?, overall=?, image_path=?,
                card_rarity=?, card_type=?, league=?, nation=?
            WHERE card_id=?
        ''', (fields['player_id'], fields['name'], fields['attack'], fields['defense'],
              fields['speed'], fields['height'], fields['club'], fields['position'],
              fields['overall'], fields['image_path'], fields['card_rarity'],
              fields['card_type'], fields['league'], fields['nation'], card_id))
        conn.commit()
        conn.close()
        flash(f'Card "{fields["name"]}" updated.', 'success')
        return redirect(url_for('cards'))

    card = conn.execute('SELECT * FROM cards WHERE card_id = ?', (card_id,)).fetchone()
    conn.close()
    if card is None:
        flash('Card not found.', 'error')
        return redirect(url_for('cards'))
    return render_template('edit_card.html', card=dict(card), rarities=RARITIES,
                           card_types=card_types, positions=POSITIONS)


@app.route('/cards/<int:card_id>/delete', methods=['POST'])
def delete_card(card_id):
    conn = get_db()
    row  = conn.execute('SELECT name FROM cards WHERE card_id = ?', (card_id,)).fetchone()
    if row:
        conn.execute('DELETE FROM cards WHERE card_id = ?', (card_id,))
        conn.commit()
        flash(f'Card "{row["name"]}" deleted.', 'success')
    else:
        flash('Card not found.', 'error')
    conn.close()
    return redirect(url_for('cards'))


# ═══════════════════════════════════════════════════════════════════════════════
# PLAYERS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/players')
def players():
    search = request.args.get('search', '').strip()
    sort   = request.args.get('sort', 'user_id')
    order  = request.args.get('order', 'asc')

    allowed = {'user_id', 'name', 'coins', 'daily_streak', 'battles_won', 'cards_dropped'}
    if sort not in allowed:
        sort = 'user_id'
    order_sql = 'DESC' if order == 'desc' else 'ASC'

    conn = get_db()
    cols = [r['name'] for r in conn.execute('PRAGMA table_info(players)').fetchall()]

    query  = 'SELECT * FROM players WHERE 1=1'
    params = []
    if search:
        query += ' AND (name LIKE ? OR CAST(user_id AS TEXT) LIKE ?)'
        params += [f'%{search}%', f'%{search}%']
    if sort in cols:
        query += f' ORDER BY {sort} {order_sql}'

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return render_template('players.html', players=rows, cols=cols,
                           search=search, sort=sort, order=order, total=len(rows))


@app.route('/players/<int:user_id>', methods=['GET', 'POST'])
def edit_player(user_id):
    conn = get_db()
    cols = [r['name'] for r in conn.execute('PRAGMA table_info(players)').fetchall()]
    readonly = {'user_id'}

    if request.method == 'POST':
        updates = {}
        for col in cols:
            if col in readonly:
                continue
            val = request.form.get(col, '').strip()
            updates[col] = val if val != '' else None
        set_clause = ', '.join(f'{c} = ?' for c in updates)
        conn.execute(f'UPDATE players SET {set_clause} WHERE user_id = ?',
                     list(updates.values()) + [user_id])
        conn.commit()
        conn.close()
        flash('Player updated.', 'success')
        return redirect(url_for('players'))

    player = conn.execute('SELECT * FROM players WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    if player is None:
        flash('Player not found.', 'error')
        return redirect(url_for('players'))
    return render_template('edit_player.html', player=dict(player),
                           cols=cols, readonly={'user_id'})


# ═══════════════════════════════════════════════════════════════════════════════
# INVENTORIES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/inventories')
def inventories():
    user_filter = request.args.get('user_id', '').strip()
    card_filter = request.args.get('card_search', '').strip()

    query = '''
        SELECT i.rowid, i.user_id, p.name AS player_name,
               i.card_id, c.name AS card_name, c.overall, c.card_rarity, i.edition
        FROM inventories i
        LEFT JOIN cards   c ON i.card_id = c.card_id
        LEFT JOIN players p ON i.user_id = p.user_id
        WHERE 1=1
    '''
    params = []
    if user_filter:
        query += ' AND (CAST(i.user_id AS TEXT) LIKE ? OR p.name LIKE ?)'
        params += [f'%{user_filter}%', f'%{user_filter}%']
    if card_filter:
        query += ' AND c.name LIKE ?'
        params.append(f'%{card_filter}%')
    query += ' ORDER BY p.name, c.name'

    conn        = get_db()
    rows        = conn.execute(query, params).fetchall()
    all_cards   = conn.execute('SELECT card_id, name, overall FROM cards ORDER BY name').fetchall()
    all_players = conn.execute('SELECT user_id, name FROM players ORDER BY name').fetchall()
    conn.close()

    return render_template('inventories.html', rows=rows, total=len(rows),
                           user_filter=user_filter, card_filter=card_filter,
                           all_cards=all_cards, all_players=all_players)


@app.route('/inventories/add', methods=['POST'])
def add_inventory():
    user_id = request.form.get('user_id', '').strip()
    card_id = request.form.get('card_id', '').strip()
    edition = request.form.get('edition', '1').strip() or '1'
    if not user_id or not card_id:
        flash('User ID and Card ID are required.', 'error')
        return redirect(url_for('inventories'))
    conn = get_db()
    conn.execute('INSERT INTO inventories (user_id, card_id, edition) VALUES (?, ?, ?)',
                 (int(user_id), int(card_id), int(edition)))
    conn.commit()
    card = conn.execute('SELECT name FROM cards WHERE card_id = ?', (card_id,)).fetchone()
    conn.close()
    flash(f'Added "{card["name"] if card else card_id}" to player {user_id}.', 'success')
    return redirect(url_for('inventories'))


@app.route('/inventories/<int:rowid>/delete', methods=['POST'])
def delete_inventory(rowid):
    conn = get_db()
    conn.execute('DELETE FROM inventories WHERE rowid = ?', (rowid,))
    conn.commit()
    conn.close()
    flash('Inventory entry removed.', 'success')
    return redirect(url_for('inventories'))


# ═══════════════════════════════════════════════════════════════════════════════
# DECKS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/decks')
def decks():
    user_filter = request.args.get('user_id', '').strip()

    query = '''
        SELECT d.rowid, d.user_id, p.name AS player_name,
               d.deck_name, d.cards
        FROM decks d
        LEFT JOIN players p ON d.user_id = p.user_id
        WHERE 1=1
    '''
    params = []
    if user_filter:
        query += ' AND (CAST(d.user_id AS TEXT) LIKE ? OR p.name LIKE ?)'
        params += [f'%{user_filter}%', f'%{user_filter}%']
    query += ' ORDER BY p.name, d.deck_name'

    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()

    annotated = []
    for row in rows:
        d = dict(row)
        d['card_count'] = len(d['cards'].split(',')) if d['cards'] else 0
        annotated.append(d)

    return render_template('decks.html', decks=annotated, user_filter=user_filter,
                           total=len(annotated))


@app.route('/decks/<int:rowid>/delete', methods=['POST'])
def delete_deck(rowid):
    conn = get_db()
    row = conn.execute('SELECT deck_name FROM decks WHERE rowid = ?', (rowid,)).fetchone()
    if row:
        conn.execute('DELETE FROM decks WHERE rowid = ?', (rowid,))
        conn.commit()
        flash(f'Deck "{row["deck_name"]}" deleted.', 'success')
    conn.close()
    return redirect(url_for('decks'))


# ═══════════════════════════════════════════════════════════════════════════════
# WISHLISTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/wishlists')
def wishlists():
    conn = get_db()
    if not table_exists(conn, 'wishlists'):
        conn.close()
        return render_template('wishlists.html', rows=[], user_filter='',
                               total=0, table_missing=True)

    user_filter = request.args.get('user_id', '').strip()
    query = '''
        SELECT w.rowid, w.user_id, p.name AS player_name,
               w.card_id, c.name AS card_name, c.overall, c.card_rarity
        FROM wishlists w
        LEFT JOIN cards   c ON w.card_id = c.card_id
        LEFT JOIN players p ON w.user_id = p.user_id
        WHERE 1=1
    '''
    params = []
    if user_filter:
        query += ' AND (CAST(w.user_id AS TEXT) LIKE ? OR p.name LIKE ?)'
        params += [f'%{user_filter}%', f'%{user_filter}%']
    query += ' ORDER BY p.name, c.name'

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return render_template('wishlists.html', rows=rows, user_filter=user_filter,
                           total=len(rows), table_missing=False)


@app.route('/wishlists/<int:rowid>/delete', methods=['POST'])
def delete_wishlist(rowid):
    conn = get_db()
    conn.execute('DELETE FROM wishlists WHERE rowid = ?', (rowid,))
    conn.commit()
    conn.close()
    flash('Wishlist entry removed.', 'success')
    return redirect(url_for('wishlists'))


# ═══════════════════════════════════════════════════════════════════════════════
# PACKS  (table: packs — one row per player, one column per pack type)
# ═══════════════════════════════════════════════════════════════════════════════

def get_pack_cols(conn):
    """Return pack column names (everything except user_id)."""
    return [r['name'] for r in conn.execute('PRAGMA table_info(packs)').fetchall()
            if r['name'] != 'user_id']


@app.route('/packs')
def packs():
    conn = get_db()
    if not table_exists(conn, 'packs'):
        conn.close()
        return render_template('packs.html', rows=[], user_filter='', total=0,
                               pack_cols=[], table_missing=True)

    user_filter = request.args.get('user_id', '').strip()
    pack_cols   = get_pack_cols(conn)

    query = '''
        SELECT pk.*, p.name AS player_name
        FROM packs pk
        LEFT JOIN players p ON pk.user_id = p.user_id
        WHERE 1=1
    '''
    params = []
    if user_filter:
        query += ' AND (CAST(pk.user_id AS TEXT) LIKE ? OR p.name LIKE ?)'
        params += [f'%{user_filter}%', f'%{user_filter}%']
    query += ' ORDER BY p.name'

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return render_template('packs.html', rows=rows, user_filter=user_filter,
                           total=len(rows), pack_cols=pack_cols, table_missing=False)


@app.route('/packs/<int:user_id>/<col>', methods=['POST'])
def edit_pack(user_id, col):
    conn = get_db()
    # Validate col against actual columns to prevent SQL injection
    valid_cols = get_pack_cols(conn)
    if col not in valid_cols:
        conn.close()
        flash('Invalid pack column.', 'error')
        return redirect(url_for('packs'))
    qty = request.form.get('quantity', '').strip()
    if not qty.lstrip('-').isdigit():
        conn.close()
        flash('Quantity must be a number.', 'error')
        return redirect(url_for('packs'))
    conn.execute(f'UPDATE packs SET {col} = ? WHERE user_id = ?', (int(qty), user_id))
    conn.commit()
    conn.close()
    flash('Pack quantity updated.', 'success')
    return redirect(url_for('packs'))


@app.route('/packs/<int:rowid>/delete', methods=['POST'])
def delete_pack(rowid):
    conn = get_db()
    conn.execute('DELETE FROM user_packs WHERE rowid = ?', (rowid,))
    conn.commit()
    conn.close()
    flash('Pack entry removed.', 'success')
    return redirect(url_for('packs'))


# ═══════════════════════════════════════════════════════════════════════════════
# ACHIEVEMENTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/achievements')
def achievements():
    conn = get_db()
    if not table_exists(conn, 'achievements'):
        conn.close()
        return render_template('achievements.html', rows=[], total=0, table_missing=True)

    rows = conn.execute('SELECT * FROM achievements ORDER BY achievement_id').fetchall()
    conn.close()
    return render_template('achievements.html', rows=rows, total=len(rows), table_missing=False)


@app.route('/achievements/add', methods=['GET', 'POST'])
def add_achievement():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        desc  = request.form.get('description', '').strip()
        if not title:
            flash('Title is required.', 'error')
            return render_template('edit_achievement.html', ach={}, is_new=True)
        conn = get_db()
        conn.execute('INSERT INTO achievements (title, description) VALUES (?, ?)', (title, desc))
        conn.commit()
        conn.close()
        flash(f'Achievement "{title}" added.', 'success')
        return redirect(url_for('achievements'))
    return render_template('edit_achievement.html', ach={}, is_new=True)


@app.route('/achievements/<int:achievement_id>', methods=['GET', 'POST'])
def edit_achievement(achievement_id):
    conn = get_db()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        desc  = request.form.get('description', '').strip()
        if not title:
            flash('Title is required.', 'error')
            ach = conn.execute('SELECT * FROM achievements WHERE achievement_id = ?',
                               (achievement_id,)).fetchone()
            conn.close()
            return render_template('edit_achievement.html', ach=dict(ach), is_new=False)
        conn.execute('UPDATE achievements SET title = ?, description = ? WHERE achievement_id = ?',
                     (title, desc, achievement_id))
        conn.commit()
        conn.close()
        flash('Achievement updated.', 'success')
        return redirect(url_for('achievements'))

    ach = conn.execute('SELECT * FROM achievements WHERE achievement_id = ?',
                       (achievement_id,)).fetchone()
    conn.close()
    if ach is None:
        flash('Achievement not found.', 'error')
        return redirect(url_for('achievements'))
    return render_template('edit_achievement.html', ach=dict(ach), is_new=False)


@app.route('/achievements/<int:achievement_id>/delete', methods=['POST'])
def delete_achievement(achievement_id):
    conn = get_db()
    row = conn.execute('SELECT title FROM achievements WHERE achievement_id = ?',
                       (achievement_id,)).fetchone()
    if row:
        conn.execute('DELETE FROM achievements WHERE achievement_id = ?', (achievement_id,))
        conn.commit()
        flash(f'Achievement "{row["title"]}" deleted.', 'success')
    conn.close()
    return redirect(url_for('achievements'))


# ═══════════════════════════════════════════════════════════════════════════════
# USER ACHIEVEMENTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/user_achievements')
def user_achievements():
    conn = get_db()
    if not table_exists(conn, 'user_achievements'):
        conn.close()
        return render_template('user_achievements.html', rows=[], user_filter='',
                               total=0, table_missing=True)

    user_filter = request.args.get('user_id', '').strip()
    query = '''
        SELECT ua.rowid, ua.user_id, p.name AS player_name,
               ua.achievement_id, a.title AS ach_title, ua.date_earned
        FROM user_achievements ua
        LEFT JOIN players     p ON ua.user_id       = p.user_id
        LEFT JOIN achievements a ON ua.achievement_id = a.achievement_id
        WHERE 1=1
    '''
    params = []
    if user_filter:
        query += ' AND (CAST(ua.user_id AS TEXT) LIKE ? OR p.name LIKE ?)'
        params += [f'%{user_filter}%', f'%{user_filter}%']
    query += ' ORDER BY p.name, ua.date_earned DESC'

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return render_template('user_achievements.html', rows=rows, user_filter=user_filter,
                           total=len(rows), table_missing=False)


@app.route('/user_achievements/<int:rowid>/delete', methods=['POST'])
def delete_user_achievement(rowid):
    conn = get_db()
    conn.execute('DELETE FROM user_achievements WHERE rowid = ?', (rowid,))
    conn.commit()
    conn.close()
    flash('User achievement removed.', 'success')
    return redirect(url_for('user_achievements'))


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _nullable(val):
    """Return None if blank, otherwise the stripped string."""
    s = (val or '').strip()
    return s if s else None

def _parse_card_form(form):
    return {
        'player_id':   _nullable(form.get('player_id')),
        'name':        form.get('name', '').strip(),       # required — keep as str
        'attack':      _int(form.get('attack')),
        'defense':     _int(form.get('defense')),
        'speed':       _int(form.get('speed')),
        'height':      _nullable(form.get('height')),
        'club':        _nullable(form.get('club')),
        'position':    _nullable(form.get('position')),
        'overall':     _int(form.get('overall')),
        'image_path':  _nullable(form.get('image_path')),
        'card_rarity': form.get('card_rarity', '').strip(), # required — keep as str
        'card_type':   form.get('card_type', 'Standard').strip(), # required — keep as str
        'league':      _nullable(form.get('league')),
        'nation':      _nullable(form.get('nation')),
    }


def _validate_card(f):
    if not f['name']:
        return 'Name is required.'
    for stat in ('attack', 'defense', 'speed', 'overall'):
        if f[stat] is None:
            return f'{stat.capitalize()} must be a number.'
        if not (0 <= f[stat] <= 99):
            return f'{stat.capitalize()} must be between 0 and 99.'
    if not f['card_rarity']:
        return 'Rarity is required.'
    if not f['card_type']:
        return 'Card type is required.'
    return None


def _int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


if __name__ == '__main__':
    print(f'Dashboard → http://localhost:5000')
    print(f'DB        → {os.path.abspath(DB_PATH)}')
    app.run(debug=True, port=5000)
