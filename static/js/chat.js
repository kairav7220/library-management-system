(function () {
    'use strict';

    var fab = document.getElementById('chatFab');
    var panel = document.getElementById('chatPanel');
    var closeBtn = document.getElementById('chatClose');
    var body = document.getElementById('chatBody');
    var form = document.getElementById('chatForm');
    var input = document.getElementById('chatInput');

    if (!fab || !panel || !form || !input) return;

    // Persistent session id so the SQLite memory keeps a continuous thread.
    var SESSION_KEY = 'lib_chat_session';
    var sessionId = localStorage.getItem(SESSION_KEY);
    if (!sessionId) {
        sessionId = 'sess-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8);
        localStorage.setItem(SESSION_KEY, sessionId);
    }

    var busy = false;

    var AGENT_ICONS = {
        'Library Director': 'fa-building-columns',
        'Catalog Librarian': 'fa-book',
        'Circulation Librarian': 'fa-repeat',
        'Membership Services': 'fa-id-card',
        'Reference Librarian': 'fa-magnifying-glass'
    };

    function loadHistory() {
        fetch('/chat/history?session_id=' + encodeURIComponent(sessionId))
            .then(function (r) { return r.json(); })
            .then(function (data) {
                (data.turns || []).forEach(function (t) {
                    if (t.user_message) addBubble(t.user_message, 'user');
                    if (t.agent_response) addBubble(t.agent_response, 'agent', t.agent_name || 'Librarian');
                });
            })
            .catch(function () { /* history is best-effort */ });
    }

    function setOpen(open) {
        panel.classList.toggle('is-open', open);
        fab.classList.toggle('is-open', open);
        panel.setAttribute('aria-hidden', open ? 'false' : 'true');
        if (open) {
            input.focus();
            scrollBottom();
            loadHistory();
        } else {
            input.blur();
        }
    }

    function scrollBottom() {
        body.scrollTop = body.scrollHeight;
    }

    function addBubble(text, who, agentName) {
        var msg = document.createElement('div');
        msg.className = 'chat-msg ' + who;

        var bubble = document.createElement('div');
        bubble.className = 'bubble';
        bubble.textContent = text;
        msg.appendChild(bubble);

        var meta = document.createElement('span');
        meta.className = 'meta';
        if (who === 'agent') {
            var icon = document.createElement('i');
            icon.className = 'fa-solid ' + (AGENT_ICONS[agentName] || 'fa-user-tie');
            icon.setAttribute('aria-hidden', 'true');
            meta.appendChild(icon);
            meta.appendChild(document.createTextNode(agentName || 'Librarian'));
            var roster = document.querySelector('.chat-roster-item[data-agent="' + agentName + '"]');
            if (roster) {
                document.querySelectorAll('.chat-roster-item').forEach(function (r) { r.classList.remove('is-active'); });
                roster.classList.add('is-active');
            }
        } else {
            meta.appendChild(document.createTextNode('You'));
        }
        msg.appendChild(meta);
        body.appendChild(msg);
        scrollBottom();
    }

    function showTyping() {
        var el = document.createElement('div');
        el.className = 'chat-typing';
        el.id = 'chatTyping';
        el.innerHTML = '<i></i><i></i><i></i>';
        el.setAttribute('aria-label', 'Librarian is typing');
        body.appendChild(el);
        scrollBottom();
        return el;
    }

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        var text = input.value.trim();
        if (!text || busy) return;

        input.value = '';
        addBubble(text, 'user');
        busy = true;
        var typing = showTyping();
        var send = form.querySelector('.chat-send');
        send.disabled = true;

        fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, session_id: sessionId })
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                typing.remove();
                addBubble(data.response || 'I could not process that request.', 'agent', data.agent || 'Library Director');
            })
            .catch(function () {
                typing.remove();
                addBubble('Sorry, I lost my train of thought. Please try again.', 'agent', 'Library Director');
            })
            .finally(function () {
                busy = false;
                send.disabled = false;
                input.focus();
            });
    });

    fab.addEventListener('click', function () {
        setOpen(!panel.classList.contains('is-open'));
    });
    closeBtn.addEventListener('click', function () { setOpen(false); });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && panel.classList.contains('is-open')) {
            setOpen(false);
        }
    });
})();
