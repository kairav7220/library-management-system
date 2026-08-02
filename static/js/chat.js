'use strict';

/* ── Session ID ───────────────────────────────────────────────────── */
var SESSION_KEY = 'lib_chat_session';
var sessionId = localStorage.getItem(SESSION_KEY);
if (!sessionId) {
    sessionId = 'sess-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8);
    localStorage.setItem(SESSION_KEY, sessionId);
}

/* ── State ────────────────────────────────────────────────────────── */
var widget, launcher, thread, input, sendBtn, badge, scrollNudge, sessionList, sessionListBody;
var busy = false;
var unreadCount = 0;
var historyLoaded = false;

/* ── Init ─────────────────────────────────────────────────────────── */
function init() {
    widget          = document.getElementById('widget');
    launcher        = document.getElementById('launcher');
    thread          = document.getElementById('thread');
    input           = document.getElementById('input');
    sendBtn         = document.getElementById('sendBtn');
    badge           = document.getElementById('badge');
    scrollNudge     = document.getElementById('scrollNudge');
    sessionList     = document.getElementById('sessionList');
    sessionListBody = document.getElementById('sessionListBody');
    if (!widget || !launcher || !thread || !input) return;

    // Set greeting timestamp
    var gt = document.getElementById('greet-time');
    if (gt) gt.textContent = now();

    // Auto-grow textarea
    input.addEventListener('input', function () {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 90) + 'px';
    });

    // Escape key handler
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && widget.classList.contains('open')) {
            if (sessionList && !sessionList.hidden) { hideSessions(); }
            else { closeWidget(); }
        }
    });

    // Scroll nudge logic
    thread.addEventListener('scroll', function () {
        var fromBottom = thread.scrollHeight - thread.scrollTop - thread.clientHeight;
        if (scrollNudge) {
            if (fromBottom > 80) scrollNudge.classList.add('visible');
            else                  scrollNudge.classList.remove('visible');
        }
    });
}

/* ── Helpers ──────────────────────────────────────────────────────── */
function now() {
    var d  = new Date();
    var h  = d.getHours();
    var m  = d.getMinutes();
    var ap = h >= 12 ? 'PM' : 'AM';
    h = h % 12 || 12;
    return h + ':' + (m < 10 ? '0' : '') + m + ' ' + ap;
}

function escapeHtml(str) {
    if (!str) return '';
    var d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

/* ── Markdown Renderer ────────────────────────────────────────────── */
function renderInline(text) {
    if (!text) return '';
    var o = escapeHtml(text);
    o = o.replace(/`([^`]+)`/g,                '<code>$1</code>');
    o = o.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    o = o.replace(/\*\*([^*]+)\*\*/g,          '<strong>$1</strong>');
    o = o.replace(/__([^_]+)__/g,              '<strong>$1</strong>');
    o = o.replace(/(^|[^\*])\*([^\*\n]+)\*(?!\*)/g, '$1<em>$2</em>');
    o = o.replace(/(^|[^_])_([^_\n]+)_(?!_)/g, '$1<em>$2</em>');
    o = o.replace(/~~([^~\n]+)~~/g,            '<del>$1</del>');
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

        // Blank line
        if (!t) { closeList(buf, listOpen); listOpen = null; i++; continue; }

        // Fenced code block
        if (/^```/.test(t)) {
            closeList(buf, listOpen); listOpen = null;
            var lang = t.slice(3).trim();
            var code = []; i++;
            while (i < lines.length && !/^```/.test(lines[i].trim())) { code.push(lines[i]); i++; }
            i++;
            buf.push('<pre><code' + (lang ? ' class="language-' + escapeHtml(lang) + '"' : '') + '>' +
                escapeHtml(code.join('\n')) + '</code></pre>');
            continue;
        }

        // Table (pipe table detection)
        if (t.indexOf('|') !== -1 && i + 1 < lines.length &&
                lines[i + 1].indexOf('|') !== -1 && /^[\s:|=-]+$/.test(lines[i + 1].trim())) {
            closeList(buf, listOpen); listOpen = null;
            var hdr = t.replace(/^\||\|$/g, '').split('|')
                .map(function (c) { return '<th>' + renderInline(c.trim()) + '</th>'; }).join('');
            i += 2;
            var rows = [];
            while (i < lines.length && /^\|/.test(lines[i].trim())) {
                var row = lines[i].trim().replace(/^\||\|$/g, '').split('|')
                    .map(function (c) { return '<td>' + renderInline(c.trim()) + '</td>'; }).join('');
                rows.push('<tr>' + row + '</tr>');
                i++;
            }
            buf.push('<div class="table-wrap"><table><thead><tr>' + hdr +
                '</tr></thead><tbody>' + rows.join('') + '</tbody></table></div>');
            continue;
        }

        // Heading
        var h = t.match(/^(#{1,6})\s+(.*)$/);
        if (h) {
            closeList(buf, listOpen); listOpen = null;
            var lvl = h[1].length;
            buf.push('<h' + lvl + '>' + renderInline(h[2]) + '</h' + lvl + '>');
            i++; continue;
        }

        // Unordered list
        var ul = t.match(/^[-*+]\s+(.*)$/);
        if (ul && t.indexOf('|') === -1) {
            if (listOpen !== 'ul') { closeList(buf, listOpen); buf.push('<ul>'); listOpen = 'ul'; }
            buf.push('<li>' + renderInline(ul[1]) + '</li>');
            i++; continue;
        }

        // Ordered list
        var ol = t.match(/^\d+[.)]\s+(.*)$/);
        if (ol) {
            if (listOpen !== 'ol') { closeList(buf, listOpen); buf.push('<ol>'); listOpen = 'ol'; }
            buf.push('<li>' + renderInline(ol[1]) + '</li>');
            i++; continue;
        }

        // Blockquote
        if (/^>/.test(t)) {
            closeList(buf, listOpen); listOpen = null;
            var quote = [];
            while (i < lines.length && /^>/.test(lines[i].trim())) {
                quote.push(lines[i].trim().replace(/^>\s?/, '')); i++;
            }
            buf.push('<blockquote>' + renderInline(quote.join('<br>')) + '</blockquote>');
            continue;
        }

        // Horizontal rule
        if (/^([-*_])\1{2,}$/.test(t)) {
            closeList(buf, listOpen); listOpen = null;
            buf.push('<hr>'); i++; continue;
        }

        // Paragraph
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

/* ── Agent dot label ──────────────────────────────────────────────── */
function agentLabel(name) {
    return '<span class="msg-label">' +
        '<span class="agent-dot" aria-hidden="true">' +
            '<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10"/></svg>' +
        '</span>' +
        escapeHtml(name || 'Library') +
    '</span>';
}

/* ── Copy icon SVG ────────────────────────────────────────────────── */
var COPY_SVG = '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<rect x="9" y="9" width="13" height="13" rx="2"/>' +
    '<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';

/* ── Add message ──────────────────────────────────────────────────── */
function addMessage(role, html, agentName) {
    var wrap = document.createElement('div');
    wrap.className = 'msg ' + role;

    var label = role === 'user'
        ? '<span class="msg-label">You</span>'
        : agentLabel(agentName);

    var copy = role === 'bot'
        ? '<button type="button" class="copy-btn" onclick="copyBubble(this)" title="Copy">' + COPY_SVG + '</button>'
        : '';

    wrap.innerHTML = label +
        '<div class="bubble">' + copy + html + '</div>' +
        '<span class="timestamp">' + now() + '</span>';

    thread.appendChild(wrap);

    // Only auto-scroll if user is near bottom
    var fromBottom = thread.scrollHeight - thread.scrollTop - thread.clientHeight;
    if (fromBottom < 120) scrollBottom();
    return wrap;
}

/* ── Greeting (fresh session) ─────────────────────────────────────── */
function showGreeting() {
    var g = document.getElementById('greeting');
    if (g) g.remove();
    var wrap = document.createElement('div');
    wrap.className = 'msg bot';
    wrap.id = 'greeting';
    wrap.innerHTML = agentLabel('Reference Librarian') +
        '<div class="welcome-card">' +
            '<p>Welcome to the <strong>Reference Desk</strong> 👋</p>' +
            '<p>I can help you find books, register members, issue &amp; return books, manage subscriptions, or pull up library stats.</p>' +
        '</div>' +
        '<span class="timestamp">' + now() + '</span>';
    thread.appendChild(wrap);
}

/* ── Typing indicator ─────────────────────────────────────────────── */
function showTyping() {
    var wrap = document.createElement('div');
    wrap.className = 'msg bot';
    wrap.id = 'chat-typing';
    wrap.innerHTML = agentLabel('Thinking…') +
        '<div class="bubble"><div class="typing"><span></span><span></span><span></span></div></div>';
    thread.appendChild(wrap);
    scrollBottom();
}
function removeTyping() {
    var el = document.getElementById('chat-typing');
    if (el) el.remove();
}

/* ── Scroll ───────────────────────────────────────────────────────── */
function scrollBottom() {
    thread.scrollTo({ top: thread.scrollHeight, behavior: 'smooth' });
    if (scrollNudge) scrollNudge.classList.remove('visible');
}

/* ── Copy button ──────────────────────────────────────────────────── */
function copyBubble(btn) {
    var bubble = btn.closest('.bubble');
    if (!bubble) return;
    var text = bubble.innerText.replace(/^Copy\s*/, '').trim();
    navigator.clipboard.writeText(text).then(function () {
        btn.classList.add('copied');
        btn.innerHTML = '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>';
        setTimeout(function () {
            btn.classList.remove('copied');
            btn.innerHTML = COPY_SVG;
        }, 1400);
    }).catch(function () {});
}

/* ── Badge ────────────────────────────────────────────────────────── */
function updateBadge() {
    if (!badge) return;
    if (unreadCount > 0) {
        badge.textContent = unreadCount > 99 ? '99+' : String(unreadCount);
        badge.hidden = false;
    } else {
        badge.hidden = true;
    }
}

/* ── Open / Close ─────────────────────────────────────────────────── */
function openWidget() {
    widget.classList.add('open');
    launcher.classList.add('hidden');
    widget.setAttribute('aria-hidden', 'false');
    hideSessions();
    unreadCount = 0;
    updateBadge();
    input.focus();
    if (!historyLoaded) { loadHistory(); historyLoaded = true; }
    else scrollBottom();
}

function closeWidget() {
    widget.classList.remove('open');
    launcher.classList.remove('hidden');
    widget.setAttribute('aria-hidden', 'true');
    input.blur();
}

/* ── Load history ─────────────────────────────────────────────────── */
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
                if (t.user_message)  addMessage('user', renderMarkdown(t.user_message));
                if (t.agent_response) addMessage('bot',  renderMarkdown(t.agent_response), t.agent_name);
            });
            scrollBottom();
        })
        .catch(function () {});
}

/* ── Reset chat ───────────────────────────────────────────────────── */
function resetChat() {
    sessionId = 'sess-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8);
    localStorage.setItem(SESSION_KEY, sessionId);
    thread.innerHTML = '';
    historyLoaded = false;
    showGreeting();
    unreadCount = 0;
    updateBadge();
    hideSessions();
    input.focus();
}

/* ── Session list ─────────────────────────────────────────────────── */
function fmtDate(iso) {
    if (!iso) return '';
    var d = new Date(iso);
    if (isNaN(d)) return '';
    var today = new Date();
    var h = d.getHours(), m = d.getMinutes(), ap = h >= 12 ? 'PM' : 'AM';
    h = h % 12 || 12;
    var time = h + ':' + (m < 10 ? '0' : '') + m + ' ' + ap;
    if (d.toDateString() === today.toDateString()) return 'Today ' + time;
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
                var item = document.createElement('button');
                item.type = 'button';
                item.className = 'session-item' + (s.session_id === sessionId ? ' current' : '');
                item.innerHTML =
                    '<span class="session-title">' + escapeHtml(s.title || 'New chat') + '</span>' +
                    (s.last_active ? '<span class="session-meta">' + fmtDate(s.last_active) + '</span>' : '');
                item.addEventListener('click', function () { loadSession(s.session_id); });
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
    historyLoaded = true;
    loadHistory();
    input.focus();
}

/* ── Send ─────────────────────────────────────────────────────────── */
function send() {
    var text = input.value.trim();
    if (!text || busy) return;
    addMessage('user', renderMarkdown(text));
    input.value = '';
    input.style.height = 'auto';
    busy = true;
    if (sendBtn) sendBtn.disabled = true;
    showTyping();

    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId })
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            removeTyping();
            addMessage('bot', renderMarkdown(data.response || 'I could not process that request.'), data.agent);
            if (!widget.classList.contains('open')) {
                unreadCount++;
                updateBadge();
            }
        })
        .catch(function () {
            removeTyping();
            addMessage('bot', renderMarkdown('Sorry, I lost connection. Please try again.'));
        })
        .finally(function () {
            busy = false;
            if (sendBtn) sendBtn.disabled = false;
            input.focus();
        });
}

/* ── Globals for inline handlers ──────────────────────────────────── */
function chipReply(el) {
    var text = (el.textContent || '').trim();
    if (!text) return;
    input.value = text;
    send();
}
function onKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
}

/* ── Boot ─────────────────────────────────────────────────────────── */
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

window.openWidget   = openWidget;
window.closeWidget  = closeWidget;
window.send         = send;
window.chipReply    = chipReply;
window.onKey        = onKey;
window.resetChat    = resetChat;
window.copyBubble   = copyBubble;
window.showSessions = showSessions;
window.hideSessions = hideSessions;
window.loadSession  = loadSession;
window.scrollBottom = scrollBottom;
