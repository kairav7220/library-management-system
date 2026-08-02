'use strict';

var SESSION_KEY = 'lib_chat_session';
var sessionId = localStorage.getItem(SESSION_KEY);
if (!sessionId) {
    sessionId = 'sess-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8);
    localStorage.setItem(SESSION_KEY, sessionId);
}

var widget, launcher, thread, input, sendBtn, badge, greeting;
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
    if (!widget || !launcher || !thread || !input) return;

    input.addEventListener('input', function () {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 80) + 'px';
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && widget.classList.contains('open')) closeWidget();
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

/* ── bot label ───────────────────────────────────────────────────── */

function botLabel(name) {
    return '<span class="msg-label"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><circle cx="12" cy="12" r="10"/></svg>' +
        escapeHtml(name || 'Reference Librarian') + '</span>';
}

/* ── add message ─────────────────────────────────────────────────── */

var COPY_SVG = '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';

function addMessage(role, html, agentName) {
    var wrap = document.createElement('div');
    wrap.className = 'msg ' + role;

    var label = role === 'user'
        ? '<span class="msg-label">You</span>'
        : botLabel(agentName);

    var copy = role === 'bot'
        ? '<button type="button" class="copy-btn" onclick="copyBubble(this)" title="Copy">' + COPY_SVG + '</button>'
        : '';

    wrap.innerHTML = label +
        '<div class="bubble">' + copy + html + '</div>' +
        '<span class="timestamp">' + now() + '</span>';

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
    wrap.innerHTML = botLabel('Reference Librarian') +
        '<div class="bubble">Welcome to the Reference Desk. Ask me to find a book, register a member, issue a book, or pull up library stats.</div>';
    thread.appendChild(wrap);
}

function showTyping() {
    var wrap = document.createElement('div');
    wrap.className = 'msg bot';
    wrap.id = 'chat-typing';
    wrap.innerHTML = botLabel('Reference Librarian') +
        '<div class="bubble"><div class="typing"><span></span><span></span><span></span></div></div>';
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

/* ── copy button ─────────────────────────────────────────────────── */

function copyBubble(btn) {
    var bubble = btn.closest('.bubble');
    if (!bubble) return;
    var text = bubble.innerText.replace(/^Copy\s*/, '').trim();
    navigator.clipboard.writeText(text).then(function () {
        btn.classList.add('copied');
        btn.innerHTML = '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>';
        setTimeout(function () {
            btn.classList.remove('copied');
            btn.innerHTML = COPY_SVG;
        }, 1200);
    });
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
    input.focus();
}

/* ── send ─────────────────────────────────────────────────────────── */

function send() {
    var text = input.value.trim();
    if (!text || busy) return;
    addMessage('user', escapeHtml(text));
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
            addMessage('bot', 'Sorry, I lost my train of thought. Please try again.');
        })
        .finally(function () {
            busy = false;
            if (sendBtn) sendBtn.disabled = false;
            input.focus();
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
window.openWidget   = openWidget;
window.closeWidget  = closeWidget;
window.send         = send;
window.chipReply    = chipReply;
window.onKey        = onKey;
window.resetChat    = resetChat;
window.copyBubble   = copyBubble;
