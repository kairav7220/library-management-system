'use strict';

// Persistent session id so the chat memory keeps a continuous thread.
var SESSION_KEY = 'lib_chat_session';
var sessionId = localStorage.getItem(SESSION_KEY);
if (!sessionId) {
    sessionId = 'sess-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8);
    localStorage.setItem(SESSION_KEY, sessionId);
}

var widget = document.getElementById('widget');
var launcher = document.getElementById('launcher');
var thread = document.getElementById('thread');
var input = document.getElementById('input');
var sendBtn = document.querySelector('.send-btn');

if (!widget || !launcher || !thread || !input) {
    window.openWidget = function () {};
    window.closeWidget = function () {};
    window.send = function () {};
    window.chipReply = function () {};
    window.onKey = function () {};
} else {
    var busy = false;

    function openWidget() {
        widget.classList.add('open');
        launcher.classList.add('hidden');
        widget.setAttribute('aria-hidden', 'false');
        loadHistory();
        input.focus();
        scrollBottom();
    }

    function closeWidget() {
        widget.classList.remove('open');
        launcher.classList.remove('hidden');
        widget.setAttribute('aria-hidden', 'true');
        input.blur();
    }

    function scrollBottom() {
        thread.scrollTop = thread.scrollHeight;
    }

    // ── Markdown renderer (safe: HTML is escaped before transforming) ──
    function escapeHtml(str) {
        var div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function renderInline(text) {
        var out = escapeHtml(text);
        out = out.replace(/`([^`]+)`/g, '<code>$1</code>');
        out = out.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
        out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        out = out.replace(/(^|[*_\W])\*([^*\n]+)\*(?!\*)/g, '$1<em>$2</em>');
        out = out.replace(/(^|\W)_([^_\n]+)_(?=\W|$)/g, '$1<em>$2</em>');
        out = out.replace(/~~([^~\n]+)~~/g, '<del>$1</del>');
        return out;
    }

    function closeList(buf, type) {
        if (type === 'ul') buf.push('</ul>');
        if (type === 'ol') buf.push('</ol>');
    }

    function renderMarkdown(text) {
        if (!text) return '';
        var lines = text.replace(/\r\n/g, '\n').split('\n');
        var buf = [];
        var listOpen = null;
        var i = 0;

        while (i < lines.length) {
            var line = lines[i];
            var t = line.trim();

            if (!t) { closeList(buf, listOpen); listOpen = null; i++; continue; }

            // Fenced code block
            if (/^```/.test(t)) {
                closeList(buf, listOpen); listOpen = null;
                var code = [];
                i++;
                while (i < lines.length && !/^```/.test(lines[i].trim())) { code.push(lines[i]); i++; }
                i++;
                buf.push('<pre><code>' + escapeHtml(code.join('\n')) + '</code></pre>');
                continue;
            }

            // Table (a pipe line whose next line is a |---| separator)
            if (t.indexOf('|') !== -1 && i + 1 < lines.length && lines[i + 1].indexOf('|') !== -1 && /^[\s:|=-]+$/.test(lines[i + 1].trim())) {
                closeList(buf, listOpen); listOpen = null;
                var header = t.replace(/^\||\|$/g, '').split('|');
                var thead = '<tr>' + header.map(function (c) { return '<th>' + renderInline(c.trim()) + '</th>'; }).join('') + '</tr>';
                i += 2;
                var tbody = [];
                while (i < lines.length && /^\|/.test(lines[i].trim())) {
                    var cells = lines[i].trim().replace(/^\||\|$/g, '').split('|');
                    tbody.push('<tr>' + cells.map(function (c) { return '<td>' + renderInline(c.trim()) + '</td>'; }).join('') + '</tr>');
                    i++;
                }
                buf.push('<div class="table-wrap"><table><thead>' + thead + '</thead><tbody>' + tbody.join('') + '</tbody></table></div>');
                continue;
            }

            // Heading
            var h = t.match(/^(#{1,6})\s+(.*)$/);
            if (h) {
                closeList(buf, listOpen); listOpen = null;
                var lvl = h[1].length;
                buf.push('<h' + lvl + '>' + renderInline(h[2]) + '</h' + lvl + '>');
                i++;
                continue;
            }

            // Unordered list
            var ul = t.match(/^[-*+]\s+(.*)$/);
            if (ul && t.indexOf('|') === -1) {
                if (listOpen !== 'ul') { closeList(buf, listOpen); buf.push('<ul>'); listOpen = 'ul'; }
                buf.push('<li>' + renderInline(ul[1]) + '</li>');
                i++;
                continue;
            }

            // Ordered list
            var ol = t.match(/^\d+[.)]\s+(.*)$/);
            if (ol) {
                if (listOpen !== 'ol') { closeList(buf, listOpen); buf.push('<ol>'); listOpen = 'ol'; }
                buf.push('<li>' + renderInline(ol[1]) + '</li>');
                i++;
                continue;
            }

            // Blockquote
            if (/^>/.test(t)) {
                closeList(buf, listOpen); listOpen = null;
                var quote = [];
                while (i < lines.length && /^>/.test(lines[i].trim())) { quote.push(lines[i].trim().replace(/^>\s?/, '')); i++; }
                buf.push('<blockquote>' + renderInline(quote.join('<br>')) + '</blockquote>');
                continue;
            }

            // Horizontal rule
            if (/^([-*_])\1{2,}$/.test(t)) {
                closeList(buf, listOpen); listOpen = null;
                buf.push('<hr>');
                i++;
                continue;
            }

            // Paragraph: consume until blank or a new block token
            closeList(buf, listOpen); listOpen = null;
            var para = [];
            while (i < lines.length) {
                var pt = lines[i].trim();
                if (pt === '' || /^```/.test(pt) || /^(#{1,6})\s/.test(pt) || /^>/.test(pt) || /^\d+[.)]\s/.test(pt) || (/^[-*+]\s/.test(pt) && pt.indexOf('|') === -1)) break;
                para.push(lines[i]);
                i++;
            }
            if (para.length) buf.push('<p>' + renderInline(para.join('\n')).replace(/\n/g, '<br>') + '</p>');
        }
        closeList(buf, listOpen);
        return buf.join('');
    }

    function botLabel(agentName) {
        return '<span class="msg-label"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><circle cx="12" cy="12" r="10"/></svg>' + escapeHtml(agentName || 'Reference Librarian') + '</span>';
    }

    function addMessage(role, html, agentName) {
        var wrap = document.createElement('div');
        wrap.className = 'msg ' + role;
        var label = role === 'user'
            ? '<span class="msg-label">You</span>'
            : botLabel(agentName);
        wrap.innerHTML = label + '<div class="bubble">' + html + '</div>';
        thread.appendChild(wrap);
        scrollBottom();
        return wrap;
    }

    function showTyping() {
        var wrap = document.createElement('div');
        wrap.className = 'msg bot';
        wrap.id = 'chat-typing';
        wrap.innerHTML = botLabel('Reference Librarian') + '<div class="bubble"><div class="typing"><span></span><span></span><span></span></div></div>';
        thread.appendChild(wrap);
        scrollBottom();
    }

    function removeTyping() {
        var el = document.getElementById('chat-typing');
        if (el) el.remove();
    }

    function loadHistory() {
        fetch('/chat/history?session_id=' + encodeURIComponent(sessionId))
            .then(function (r) { return r.json(); })
            .then(function (data) {
                var turns = data.turns || [];
                if (turns.length) {
                    // A thread already exists: drop the static greeting so it
                    // does not duplicate on every reopen.
                    var greeting = thread.querySelector('.msg.bot');
                    if (greeting) greeting.remove();
                }
                turns.forEach(function (t) {
                    if (t.user_message) addMessage('user', escapeHtml(t.user_message));
                    if (t.agent_response) addMessage('bot', renderMarkdown(t.agent_response), t.agent_name);
                });
            })
            .catch(function () { /* history is best-effort */ });
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

        fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, session_id: sessionId })
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                removeTyping();
                addMessage('bot', renderMarkdown(data.response || 'I could not process that request.'), data.agent);
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

    function chipReply(el) {
        var text = (el.textContent || '').trim();
        if (!text) return;
        input.value = text;
        send();
    }

    function onKey(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            send();
        }
    }

    input.addEventListener('input', function () {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 80) + 'px';
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && widget.classList.contains('open')) closeWidget();
    });

    window.openWidget = openWidget;
    window.closeWidget = closeWidget;
    window.send = send;
    window.chipReply = chipReply;
    window.onKey = onKey;
}
