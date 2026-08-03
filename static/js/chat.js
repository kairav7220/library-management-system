'use strict';

var SESSION_KEY = 'lib_chat_session';
var sessionId = localStorage.getItem(SESSION_KEY);
if (!sessionId) {
    sessionId = 'sess-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8);
    localStorage.setItem(SESSION_KEY, sessionId);
}

var widget, launcher, thread, input, sendBtn, badge, greeting, sessionList, sessionListBody;
var busy = false;
var unreadCount = 0;

function init() {
    widget   = document.getElementById('widget');
    launcher = document.getElementById('launcher');
    thread   = document.getElementById('thread');
    input    = document.getElementById('input');
    sendBtn  = document.querySelector('.send-btn');
    badge    = document.getElementById('badge');
    greeting = document.getElementById('greeting');
    sessionList     = document.getElementById('sessionList');
    sessionListBody = document.getElementById('sessionListBody');
    if (!widget || !launcher || !thread || !input) return;

    input.addEventListener('input', function () {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 80) + 'px';
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && widget.classList.contains('open')) {
            if (sessionList && !sessionList.hidden) { hideSessions(); }
            else { closeWidget(); }
        }
    });
}

/* ── helpers ─────────────────────────────────────────────────────── */

function now() {
    var d = new Date();
    var h = d.getHours();
    var m = d.getMinutes();
    var ap = h >= 12 ? 'PM' : 'AM';
    h = h % 12 || 12;
    return h + ':' + (m < 10 ? '0' : '') + m + ' ' + ap;
}

function escapeHtml(str) {
    var d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

/* ── markdown renderer (HTML-escaped before transforming) ────────── */

function renderInline(text) {
    var o = escapeHtml(text);
    o = o.replace(/`([^`]+)`/g, '<code>$1</code>');
    o = o.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    o = o.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    o = o.replace(/(^|[*_\W])\*([^*\n]+)\*(?!\*)/g, '$1<em>$2</em>');
    o = o.replace(/(^|\W)_([^_\n]+)_(?=\W|$)/g, '$1<em>$2</em>');
    o = o.replace(/~~([^~\n]+)~~/g, '<del>$1</del>');
    return o;
}

function closeList(buf, type) {
    if (type === 'ul') buf.push('</ul>');
    if (type === 'ol') buf.push('</ol>');
}

function renderMarkdown(text) {
    if (!text) return '';
    var lines = text.replace(/\r\n/g, '\n').split('\n');
    var buf = [], listOpen = null, i = 0;

    while (i < lines.length) {
        var t = lines[i].trim();
        if (!t) { closeList(buf, listOpen); listOpen = null; i++; continue; }
        if (/^```/.test(t)) {
            closeList(buf, listOpen); listOpen = null;
            var code = []; i++;
            while (i < lines.length && !/^```/.test(lines[i].trim())) { code.push(lines[i]); i++; }
            i++;
            buf.push('<pre><code>' + escapeHtml(code.join('\n')) + '</code></pre>');
            continue;
        }
        if (t.indexOf('|') !== -1 && i + 1 < lines.length &&
            lines[i + 1].indexOf('|') !== -1 && /^[\s:|=-]+$/.test(lines[i + 1].trim())) {
            closeList(buf, listOpen); listOpen = null;
            var hdr = t.replace(/^\||\|$/g, '').split('|')
                .map(function (c) { return '<th>' + renderInline(c.trim()) + '</th>'; }).join('');
            i += 2;
            var tbody = [];
            while (i < lines.length && /^\|/.test(lines[i].trim())) {
                var row = lines[i].trim().replace(/^\||\|$/g, '').split('|')
                    .map(function (c) { return '<td>' + renderInline(c.trim()) + '</td>'; }).join('');
                tbody.push('<tr>' + row + '</tr>');
                i++;
            }
            buf.push('<div class="table-wrap"><table><thead><tr>' + hdr +
                '</tr></thead><tbody>' + tbody.join('') + '</tbody></table></div>');
            continue;
        }
        var h = t.match(/^(#{1,6})\s+(.*)$/);
        if (h) {
            closeList(buf, listOpen); listOpen = null;
            var lvl = h[1].length;
            buf.push('<h' + lvl + '>' + renderInline(h[2]) + '</h' + lvl + '>');
            i++; continue;
        }
        var ul = t.match(/^[-*+]\s+(.*)$/);
        if (ul && t.indexOf('|') === -1) {
            if (listOpen !== 'ul') { closeList(buf, listOpen); buf.push('<ul>'); listOpen = 'ul'; }
            buf.push('<li>' + renderInline(ul[1]) + '</li>');
            i++; continue;
        }
        var ol = t.match(/^\d+[.)]\s+(.*)$/);
        if (ol) {
            if (listOpen !== 'ol') { closeList(buf, listOpen); buf.push('<ol>'); listOpen = 'ol'; }
            buf.push('<li>' + renderInline(ol[1]) + '</li>');
            i++; continue;
        }
        if (/^>/.test(t)) {
            closeList(buf, listOpen); listOpen = null;
            var quote = [];
            while (i < lines.length && /^>/.test(lines[i].trim())) { quote.push(lines[i].trim().replace(/^>\s?/, '')); i++; }
            buf.push('<blockquote>' + renderInline(quote.join('<br>')) + '</blockquote>');
            continue;
        }
        if (/^([-*_])\1{2,}$/.test(t)) {
            closeList(buf, listOpen); listOpen = null;
            buf.push('<hr>'); i++; continue;
        }
        closeList(buf, listOpen); listOpen = null;
        var para = [];
        while (i < lines.length) {
            var pt = lines[i].trim();
            if (pt === '' || /^```/.test(pt) || /^#{1,6}\s/.test(pt) || /^>/.test(pt) ||
                /^\d+[.)]\s/.test(pt) || (/^[-*+]\s/.test(pt) && pt.indexOf('|') === -1)) break;
            para.push(lines[i]); i++;
        }
        if (para.length) buf.push('<p>' + renderInline(para.join('\n')).replace(/\n/g, '<br>') + '</p>');
    }
    closeList(buf, listOpen);
    return buf.join('');
}

/* ── message building ────────────────────────────────────────────── */

var BOT_AVATAR = '<div class="avatar avatar-bot"><span class="material-symbols-outlined">smart_toy</span></div>';

function addMessage(role, html, agentName) {
    var wrap = document.createElement('div');
    wrap.className = 'msg ' + role;

    var bubble = '<div class="bubble">' + html + '</div>';
    var timestamp = '<span class="timestamp">' + now() + '</span>';

    if (role === 'user') {
        wrap.innerHTML = bubble + timestamp;
    } else {
        wrap.innerHTML = '<div class="msg-row">' + BOT_AVATAR + bubble + '</div>' +
            timestamp;
    }
    thread.appendChild(wrap);
    scrollBottom();
    return wrap;
}

function showGreeting() {
    var g = document.getElementById('greeting');
    if (g) g.remove();
    var wrap = document.createElement('div');
    wrap.className = 'msg bot';
    wrap.id = 'greeting';
    wrap.innerHTML = '<div class="msg-row">' + BOT_AVATAR +
        '<div class="bubble">Welcome to the Reference Desk. Ask me to find a book, register a member, issue a book, or pull up library stats.</div></div>';
    thread.appendChild(wrap);
}

function showTyping() {
    var wrap = document.createElement('div');
    wrap.className = 'msg bot';
    wrap.id = 'chat-typing';
    wrap.innerHTML = '<div class="msg-row typing-row">' + BOT_AVATAR +
        '<span class="typing-label">Library Assistant is typing...</span></div>';
    thread.appendChild(wrap);
    scrollBottom();
}

function removeTyping() {
    var el = document.getElementById('chat-typing');
    if (el) el.remove();
}

function scrollBottom() {
    thread.scrollTop = thread.scrollHeight;
}

/* ── unread badge ─────────────────────────────────────────────────── */

function updateBadge() {
    if (!badge) return;
    if (unreadCount > 0) {
        badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
        badge.hidden = false;
    } else {
        badge.hidden = true;
    }
}

/* ── open / close ─────────────────────────────────────────────────── */

function openWidget() {
    widget.classList.add('open');
    launcher.classList.add('hidden');
    widget.setAttribute('aria-hidden', 'false');
    hideSessions();
    unreadCount = 0;
    updateBadge();
    input.focus();
    scrollBottom();
    loadHistory();
}

function closeWidget() {
    widget.classList.remove('open');
    launcher.classList.remove('hidden');
    widget.setAttribute('aria-hidden', 'true');
    input.blur();
}

/* ── history ──────────────────────────────────────────────────────── */

function loadHistory() {
    fetch('/chat/history?session_id=' + encodeURIComponent(sessionId))
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var turns = data.turns || [];
            if (turns.length) {
                var g = document.getElementById('greeting');
                if (g) g.remove();
            }
            turns.forEach(function (t) {
                if (t.user_message) addMessage('user', escapeHtml(t.user_message));
                if (t.agent_response) addMessage('bot', renderMarkdown(t.agent_response), t.agent_name);
            });
        })
        .catch(function () {});
}

/* ── reset chat ───────────────────────────────────────────────────── */

function resetChat() {
    sessionId = 'sess-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8);
    localStorage.setItem(SESSION_KEY, sessionId);
    thread.innerHTML = '';
    showGreeting();
    unreadCount = 0;
    updateBadge();
    hideSessions();
    input.focus();
}

/* ── session list (history) ──────────────────────────────────────── */

function fmtDate(iso) {
    if (!iso) return '';
    var d = new Date(iso);
    if (isNaN(d)) return '';
    var today = new Date();
    var sameDay = d.toDateString() === today.toDateString();
    var h = d.getHours(), m = d.getMinutes(), ap = h >= 12 ? 'PM' : 'AM';
    h = h % 12 || 12;
    var time = h + ':' + (m < 10 ? '0' : '') + m + ' ' + ap;
    if (sameDay) return 'Today ' + time;
    var yest = new Date(today);
    yest.setDate(today.getDate() - 1);
    if (d.toDateString() === yest.toDateString()) return 'Yesterday ' + time;
    return d.toLocaleDateString() + ' ' + time;
}

function showSessions() {
    if (!sessionList || !sessionListBody) return;
    sessionListBody.innerHTML = '<div class="session-empty">Loading conversations…</div>';
    thread.style.display = 'none';
    sessionList.hidden = false;

    fetch('/chat/sessions')
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var sessions = data.sessions || [];
            if (!sessions.length) {
                sessionListBody.innerHTML = '<div class="session-empty">No past conversations yet.</div>';
                return;
            }
            sessionListBody.innerHTML = '';
            sessions.forEach(function (s) {
                var item = document.createElement('div');
                item.className = 'session-item' + (s.session_id === sessionId ? ' current' : '');

                var main = document.createElement('button');
                main.type = 'button';
                main.className = 'session-main';
                var title = escapeHtml(s.title || 'New chat');
                var meta = fmtDate(s.last_active) || '';
                main.innerHTML = '<span class="session-title">' + title + '</span>' +
                    (meta ? '<span class="session-meta">' + meta + '</span>' : '');
                main.addEventListener('click', function () { loadSession(s.session_id); });

                var del = document.createElement('button');
                del.type = 'button';
                del.className = 'session-del';
                del.title = 'Delete conversation';
                del.setAttribute('aria-label', 'Delete conversation');
                del.innerHTML = '<span class="material-symbols-outlined">delete</span>';
                del.addEventListener('click', function (e) {
                    e.stopPropagation();
                    deleteSession(s.session_id, del);
                });

                item.appendChild(main);
                item.appendChild(del);
                sessionListBody.appendChild(item);
            });
        })
        .catch(function () {
            sessionListBody.innerHTML = '<div class="session-empty">Could not load conversations.</div>';
        });
}

function hideSessions() {
    if (!sessionList) return;
    sessionList.hidden = true;
    thread.style.display = '';
}

function loadSession(id) {
    sessionId = id;
    localStorage.setItem(SESSION_KEY, sessionId);
    unreadCount = 0;
    updateBadge();
    thread.innerHTML = '';
    hideSessions();
    showGreeting();
    loadHistory();
    input.focus();
}

function deleteSession(id, btn) {
    if (!btn) return;
    btn.classList.add('busy');
    btn.disabled = true;
    fetch('/chat/sessions/' + encodeURIComponent(id), { method: 'DELETE' })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var item = btn.closest('.session-item');
            if (item) item.remove();
            if (id === sessionId) {
                sessionId = 'sess-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8);
                localStorage.setItem(SESSION_KEY, sessionId);
            }
            if (!sessionListBody.querySelector('.session-item')) {
                sessionListBody.innerHTML = '<div class="session-empty">No past conversations yet.</div>';
            }
        })
        .catch(function () {
            btn.classList.remove('busy');
            btn.disabled = false;
        });
}

/* ── send (streaming) ─────────────────────────────────────────────── */

function parseSSE(chunk, handlers) {
    var text = new TextDecoder().decode(chunk);
    text.split('\n').forEach(function (line) {
        line = line.replace(/\r$/, '');
        if (line.indexOf('data: ') === 0) {
            var payload = line.slice(6);
            try {
                var evt = JSON.parse(payload);
                if (evt.type === 'delta' && evt.text) handlers.delta(evt.text);
                else if (evt.type === 'done') handlers.done(evt);
                else if (evt.type === 'error') handlers.error(new Error(evt.message || 'Stream error'));
            } catch (e) {}
        }
    });
}

function send() {
    var text = input.value.trim();
    if (!text || busy) return;
    addMessage('user', escapeHtml(text));
    input.value = '';
    input.style.height = 'auto';
    busy = true;
    if (sendBtn) sendBtn.disabled = true;
    showTyping();

    var wrap = null;
    var bubble = null;
    var raw = '';
    var agentName = null;
    var finished = false;
    var failed = false;

    function finish() {
        if (finished) return;
        finished = true;
        busy = false;
        if (sendBtn) sendBtn.disabled = false;
        removeTyping();
        var html = raw ? renderMarkdown(raw) : (failed ? 'Sorry, I lost my train of thought. Please try again.' : 'I could not process that request.');
        if (wrap && bubble) {
            bubble.innerHTML = html;
            bubble.classList.remove('streaming');
        } else {
            addMessage('bot', html, agentName);
        }
        if (bubble && raw) scrollBottom();
        if (!widget.classList.contains('open')) {
            unreadCount++;
            updateBadge();
        }
        input.focus();
    }

    fetch('/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId })
    })
        .then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.body.getReader();
        })
        .then(function (reader) {
            removeTyping();
            wrap = addMessage('bot', '', agentName);
            bubble = wrap.querySelector('.bubble');
            bubble.classList.add('streaming');
            scrollBottom();

            function pump() {
                return reader.read().then(function (res) {
                    if (res.done) { finish(); return; }
                    parseSSE(res.value, {
                        delta: function (t) {
                            raw += t;
                            bubble.textContent = raw;
                            scrollBottom();
                        },
                        done: function (evt) {
                            raw = evt.response || raw;
                            agentName = evt.agent || null;
                            finish();
                        },
                        error: function (e) {
                            failed = true;
                            finish();
                        }
                    });
                    return pump();
                });
            }
            return pump();
        })
        .catch(function () {
            failed = true;
            finish();
        });
}

/* ── globals for inline handlers ──────────────────────────────────── */

function chipReply(el) {
    var text = (el.textContent || '').trim();
    if (!text) return;
    input.value = text;
    send();
}
function onKey(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }

/* ── boot ─────────────────────────────────────────────────────────── */

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
window.openWidget    = openWidget;
window.closeWidget   = closeWidget;
window.send          = send;
window.chipReply     = chipReply;
window.onKey         = onKey;
window.resetChat     = resetChat;
window.showSessions  = showSessions;
window.hideSessions  = hideSessions;
window.loadSession   = loadSession;
window.deleteSession = deleteSession;
