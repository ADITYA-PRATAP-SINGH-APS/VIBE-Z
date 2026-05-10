const menuToggle = document.getElementById("menuToggle");
const sidebar = document.getElementById("sidebar");
const themeToggle = document.getElementById("themeToggle");
const toast = document.getElementById("toast");
const searchInput = document.getElementById("searchInput");
const searchSuggestions = document.getElementById("searchSuggestions");

if (menuToggle) {
  menuToggle.addEventListener("click", () => {
    sidebar.classList.toggle("open");
  });
}

const storedTheme = localStorage.getItem("theme") || "dark";
document.body.classList.toggle("theme-dark", storedTheme === "dark");
document.body.classList.toggle("theme-light", storedTheme === "light");

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const isLight = document.body.classList.contains("theme-light");
    document.body.classList.toggle("theme-light", !isLight);
    document.body.classList.toggle("theme-dark", isLight);
    localStorage.setItem("theme", isLight ? "dark" : "light");
    showToast("Theme updated");
  });
}

const toastQueue = [];
let toastActive = false;

function showToast(message, tone = "success") {
  if (!toast) return;
  const text = String(message || "").trim();
  if (!text) return;
  toastQueue.push({ text, tone });
  if (!toastActive) runNextToast();
}

function runNextToast() {
  if (!toast || toastQueue.length === 0) {
    toastActive = false;
    return;
  }
  toastActive = true;
  const { text, tone } = toastQueue.shift();

  toast.classList.remove("error", "info");
  if (tone === "error") toast.classList.add("error");
  if (tone === "info") toast.classList.add("info");

  toast.textContent = text;
  toast.classList.add("show");

  window.setTimeout(() => {
    toast.classList.remove("show");
    window.setTimeout(runNextToast, 240);
  }, 2200);
}

document.querySelectorAll("[data-toast]").forEach((btn) => {
  btn.addEventListener("click", () => showToast(btn.dataset.toast, "info"));
});

// Convert Django messages to toasts (prevents double UI clutter)
const messageStack = document.querySelector(".message-stack");
if (messageStack) {
  messageStack.querySelectorAll(".message").forEach((msg) => {
    const tone = msg.classList.contains("error") ? "error" : "success";
    showToast(msg.textContent, tone);
  });
  messageStack.remove();
}

// Report widget UX (animated panel + loading state)
document.querySelectorAll("[data-report-widget]").forEach((widget) => {
  const openBtn = widget.querySelector("[data-report-open]");
  const panel = widget.querySelector("[data-report-panel]");
  const cancelBtn = widget.querySelector("[data-report-cancel]");
  const form = widget.querySelector("[data-report-form]");
  const submitBtn = widget.querySelector("[data-report-submit]");
  const reasonField = widget.querySelector("textarea[name='reason'], input[name='reason']");

  if (!openBtn || !panel) return;

  const open = () => {
    panel.classList.add("open");
    panel.setAttribute("aria-hidden", "false");
    openBtn.setAttribute("aria-expanded", "true");
    if (reasonField) reasonField.focus({ preventScroll: true });
  };

  const close = () => {
    panel.classList.remove("open", "shake");
    panel.setAttribute("aria-hidden", "true");
    openBtn.setAttribute("aria-expanded", "false");
    if (reasonField) reasonField.value = "";
  };

  openBtn.addEventListener("click", () => {
    if (panel.classList.contains("open")) close();
    else open();
  });

  if (cancelBtn) cancelBtn.addEventListener("click", close);

  if (form) {
    form.addEventListener("submit", (e) => {
      // Let browser show required-message UX, but add a subtle shake.
      if (!form.checkValidity()) {
        e.preventDefault();
        form.reportValidity();
        panel.classList.add("shake");
        window.setTimeout(() => panel.classList.remove("shake"), 280);
        return;
      }

      if (submitBtn) {
        submitBtn.classList.add("is-loading");
        submitBtn.disabled = true;
      }
      if (cancelBtn) cancelBtn.disabled = true;
      if (openBtn) openBtn.disabled = true;
    });
  }
});

if (searchInput && searchSuggestions) {
  const suggestions = ["@luna", "@astro", "@nova", "@vibez", "coding", "gaming", "design"];
  searchInput.addEventListener("input", () => {
    const value = searchInput.value.trim();
    if (!value) {
      searchSuggestions.classList.remove("active");
      return;
    }
    searchSuggestions.innerHTML = "";
    suggestions
      .filter((item) => item.toLowerCase().includes(value.toLowerCase()))
      .slice(0, 5)
      .forEach((item) => {
        const div = document.createElement("div");
        div.textContent = item;
        div.addEventListener("click", () => {
          searchInput.value = item;
          searchSuggestions.classList.remove("active");
        });
        searchSuggestions.appendChild(div);
      });
    searchSuggestions.classList.add("active");
  });
}

const infiniteContainers = document.querySelectorAll("[data-infinite]");
infiniteContainers.forEach((container) => {
  window.addEventListener("scroll", () => {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 200) {
      const skeleton = document.createElement("div");
      skeleton.className = "skeleton";
      container.appendChild(skeleton);
      setTimeout(() => skeleton.remove(), 1200);
    }
  });
});

// Home topic quote (chat/gaming/coding etc.)
const quoteEl = document.querySelector("[data-topic-quote] .funky-quote-text");
if (quoteEl) {
  const quotes = [
    "“GG in the chat — push the commit and ping the squad.”",
    "“/msg me after the raid — I’ve got the patch notes.”",
    "“Ship it, then drop the link in chat.”",
    "“Lag spike? Nah, that’s just the Wi‑Fi doing parkour.”",
    "“BRB, rebuilding… then back to the lobby.”",
    "“Console.log it. Screenshot it. Send it.”",
    "“New bug unlocked: it only happens on your machine.”",
    "“Stack trace says hi. So does the group chat.”",
    "“Queue popped — deploy later, match now.”",
    "“One more game, one more commit, one more message.”",
    "“Hotfix in progress — don’t @ me, I’m in ranked.”",
    "“Merge conflict: my code vs your vibe.”",
    "“Drop the repo link and meet me in the lobby.”",
    "“Ping me when the build turns green.”",
    "“Patch notes: chat spam reduced by 0%.”",
    "“POV: you said ‘one last game’ and opened a new PR.”",
    "“Type faster — the boss fight is loading.”",
    "“AFK? Nah. Just refactoring.”",
    "“If it works, don’t touch it. If it’s ugly, ship it.”",
    "“BRB, updating dependencies and my personality.”",
    "“Clip that. Then commit that.”",
    "“FPS dropped, confidence dropped, still queued.”",
    "“Your mic is muted… so is my patience.”",
    "“I didn’t rage quit — I force-closed the app.”",
    "“Send the screenshot, I’ll send the fix.”",
    "“Stand back, I’m about to run it in production.”",
    "“Git pull first, then pull up in chat.”",
    "“I only speak in emojis and stack traces.”",
    "“New message: ‘deploy?’ — seen 2 days ago.”",
    "“Respectfully, that’s a skill issue and a null pointer.”",
    "“Lobby rule: no spoilers, no spoilers, no spoilers.”",
    "“Code review energy: explain it like I’m your teammate.”",
  ];

  const key = "vibez_last_quote";
  const last = Number(localStorage.getItem(key) || "-1");
  let idx = Math.floor(Math.random() * quotes.length);
  if (quotes.length > 1 && idx === last) {
    idx = (idx + 1) % quotes.length;
  }
  localStorage.setItem(key, String(idx));
  quoteEl.textContent = quotes[idx];
}

// Global incoming call popup (works on every page)
(function initGlobalIncomingCalls() {
  const userId = window.VIBEZ_USER_ID;
  const popup = document.getElementById("globalCallPopup");
  if (!userId || !popup) return;

  const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${wsScheme}://${window.location.host}/ws/calls/u-${userId}/`);

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
  }

  function hidePopup() {
    popup.classList.remove("show");
    popup.setAttribute("aria-hidden", "true");
    popup.innerHTML = "";
  }

  async function post(url) {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCookie("csrftoken"),
      },
    });

    let data = null;
    try {
      data = await res.json();
    } catch {
      // ignore
    }

    if (!res.ok) {
      const code = res.status ? ` (${res.status})` : "";
      throw new Error(`request failed${code}`);
    }

    return data || {};
  }

  function showIncoming(call) {
    const caller = call.caller && call.caller.unique_name ? call.caller.unique_name : "Someone";
    const type = call.call_type || "audio";

    popup.innerHTML = `
      <div>
        <strong>Incoming ${type} call</strong>
        <div class="muted">@${caller} is calling you…</div>
      </div>
      <div class="button-row">
        <button class="button primary" type="button" data-accept>Accept</button>
        <button class="button danger" type="button" data-decline>Decline</button>
      </div>
    `;

    popup.classList.add("show");
    popup.setAttribute("aria-hidden", "false");

    const acceptBtn = popup.querySelector("[data-accept]");
    const declineBtn = popup.querySelector("[data-decline]");

    if (acceptBtn) {
      acceptBtn.addEventListener("click", async () => {
        try {
          acceptBtn.disabled = true;
          const data = await post(`/calls/accept/${call.session_id}/`);
          hidePopup();
          if (data.redirect) {
            window.location.href = data.redirect;
          } else {
            window.location.href = `/calls/?room=${call.room}`;
          }
        } catch {
          showToast("Could not accept call", "error");
          acceptBtn.disabled = false;
        }
      });
    }

    if (declineBtn) {
      declineBtn.addEventListener("click", async () => {
        try {
          declineBtn.disabled = true;
          await post(`/calls/decline/${call.session_id}/`);
          hidePopup();
          showToast("Call declined", "info");
        } catch {
          showToast("Could not decline", "error");
          declineBtn.disabled = false;
        }
      });
    }
  }

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.event === "incoming_call") {
        // Safety: never show incoming popup to the caller (or wrong user)
        const uid = String(userId);
        const callerId = data.caller && data.caller.id != null ? String(data.caller.id) : "";
        const calleeId = data.callee && data.callee.id != null ? String(data.callee.id) : "";
        if (callerId && callerId === uid) return;
        if (calleeId && calleeId !== uid) return;
        showIncoming(data);
      }
      if (data.event === "hangup" || data.event === "call_declined") {
        hidePopup();
      }
    } catch {
      // ignore
    }
  };

  socket.onerror = () => {
    // silent
  };
})();
