const messagesEl = document.getElementById("messages");
const messagesScrollEl = document.getElementById("messages-scroll");
const emptyState = document.getElementById("empty-state");
const greetingEl = document.getElementById("greeting");
const suggestionsEl = document.getElementById("suggestions");
const chatListEl = document.getElementById("chat-list");
const input = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const micBtn = document.getElementById("mic-btn");
const newChatBtn = document.getElementById("new-chat-btn");
const brandEl = document.getElementById("brand");
const brandLabel = document.getElementById("brand-label");
const brandDropdown = document.getElementById("brand-dropdown");
const starfieldCanvas = document.getElementById("starfield-canvas");
const starCtx = starfieldCanvas.getContext("2d");
const moonIcon = document.getElementById("moon-icon");

const nebulaView = document.getElementById("nebula-view");
const healthView = document.getElementById("health-view");
const healthSidebar = document.getElementById("health-sidebar");
const healthTodayTotal = document.getElementById("health-today-total");
const healthLogList = document.getElementById("health-log-list");
const healthMessagesScrollEl = document.getElementById("health-messages-scroll");
const healthEmptyState = document.getElementById("health-empty-state");
const healthPhotoInput = document.getElementById("health-photo-input");
const healthPhotoBtn = document.getElementById("health-photo-btn");
const healthInput = document.getElementById("health-message-input");
const healthSendBtn = document.getElementById("health-send-btn");
const healthPreview = document.getElementById("health-preview");
const workspaceLabel = document.getElementById("workspace-label");
const workspaceSub = document.getElementById("workspace-sub");
const topbarTip = document.getElementById("topbar-tip");

const SUGGESTIONS = [
  "Summarize this week's notes",
  "What have I been doing to improve my health?",
  "Who is the current CEO of OpenAI?",
];

// Each planet is rendered as a big DOM/CSS sphere peeking in from the top-right
// corner (matching the reference design), not a small canvas sprite. `PLANETS`
// keys are what /nova <planet> matches against; presence in this object is what
// makes a word a "valid" planet argument.
const PLANET_SCENES = {
  mercury: {
    sphereBackground: "radial-gradient(circle at 35% 30%, #c9c2b3 0%, #8f887a 55%, #6b6560 100%)",
    ambientTint: "rgba(140, 132, 118, 0.35)",
    glowColor: "rgba(160, 150, 130, 0.12)",
    overlays: [
      { top: "30%", left: "20%", w: "10%", h: "7%", color: "rgba(0,0,0,0.25)" },
      { top: "55%", left: "55%", w: "8%", h: "6%", color: "rgba(0,0,0,0.22)" },
      { top: "70%", left: "30%", w: "6%", h: "5%", color: "rgba(0,0,0,0.2)" },
      { top: "20%", left: "62%", w: "7%", h: "5%", color: "rgba(0,0,0,0.2)" },
    ],
  },
  venus: {
    sphereBackground: "repeating-linear-gradient(100deg, #f0dda0 0px, #e6cf8c 35px, #d8bd76 35px, #d8bd76 65px, #f0dda0 65px, #f0dda0 100px)",
    sphereFilter: "saturate(0.75) brightness(0.92)",
    ambientTint: "rgba(200, 180, 120, 0.4)",
    glowColor: "rgba(220, 200, 140, 0.14)",
  },
  earth: {
    sphereBackground: "radial-gradient(circle at 35% 30%, #6ba7e8 0%, #2f5fa8 55%, #16305c 100%)",
    ambientTint: "rgba(60, 110, 180, 0.4)",
    glowColor: "rgba(90, 150, 220, 0.16)",
    overlays: [
      { top: "30%", left: "15%", w: "30%", h: "20%", color: "rgba(70,140,60,0.75)", radius: "40% 60% 55% 45%" },
      { top: "60%", left: "55%", w: "22%", h: "16%", color: "rgba(90,120,55,0.7)", radius: "50% 50% 40% 60%" },
      { top: "15%", left: "50%", w: "26%", h: "10%", color: "rgba(255,255,255,0.35)" },
      { top: "68%", left: "20%", w: "20%", h: "8%", color: "rgba(255,255,255,0.3)" },
    ],
  },
  mars: {
    sphereBackground: "radial-gradient(circle at 35% 30%, #e2916a 0%, #b5502a 55%, #7a2f13 100%)",
    ambientTint: "rgba(190, 90, 50, 0.4)",
    glowColor: "rgba(210, 110, 70, 0.16)",
    overlays: [
      { top: "45%", left: "20%", w: "28%", h: "10%", color: "rgba(90,40,20,0.4)" },
      { top: "25%", left: "55%", w: "14%", h: "10%", color: "rgba(70,30,15,0.3)" },
    ],
  },
  jupiter: {
    sphereBackground: "repeating-linear-gradient(96deg, #d9c6a8 0px, #cdb392 26px, #b8926a 26px, #b8926a 46px, #c9a578 46px, #c9a578 74px, #a67a54 74px, #a67a54 96px, #d6bd97 96px, #d6bd97 130px, #93684a 130px, #93684a 150px)",
    sphereFilter: "saturate(0.65) brightness(0.62)",
    ambientTint: "rgba(60, 58, 50, 0.55)",
    glowColor: "rgba(180, 140, 90, 0.10)",
    overlays: [
      { top: "38%", left: "12%", w: "34%", h: "12%", color: "rgba(120,60,40,0.35)", blur: "6px" },
    ],
  },
  saturn: {
    sphereBackground: "repeating-linear-gradient(94deg, #ecdcae 0px, #e4d29c 30px, #d8c088 30px, #d8c088 55px, #cbb379 55px, #cbb379 80px, #e4d29c 80px, #e4d29c 110px)",
    sphereFilter: "saturate(0.7) brightness(0.85)",
    ambientTint: "rgba(200, 180, 130, 0.4)",
    glowColor: "rgba(210, 190, 140, 0.14)",
    rings: { faint: false },
  },
  uranus: {
    sphereBackground: "radial-gradient(circle at 35% 30%, #c3ece5 0%, #7cc9bd 55%, #5fa89e 100%)",
    ambientTint: "rgba(120, 200, 190, 0.3)",
    glowColor: "rgba(140, 220, 210, 0.14)",
    rings: { faint: true },
  },
  neptune: {
    sphereBackground: "radial-gradient(circle at 35% 30%, #5170d9 0%, #2c47a0 55%, #1c2f66 100%)",
    ambientTint: "rgba(50, 80, 180, 0.4)",
    glowColor: "rgba(80, 110, 210, 0.14)",
    overlays: [
      { top: "35%", left: "25%", w: "18%", h: "12%", color: "rgba(15,25,60,0.5)" },
    ],
  },
};
const PLANETS = PLANET_SCENES;

function buildPlanetSceneHTML(planetKey) {
  const cfg = PLANET_SCENES[planetKey];
  if (!cfg) return "";

  const size = 640;
  const offset = -Math.round(size * 0.28);
  const filter = cfg.sphereFilter || "none";
  const boxShadow = "inset -60px -40px 120px rgba(0,0,0,0.5), inset 30px 20px 80px rgba(255,255,255,0.08)";

  const overlaysHtml = (cfg.overlays || []).map(o => {
    const blurStyle = o.blur ? `filter: blur(${o.blur});` : "";
    return `<div style="position:absolute; top:${o.top}; left:${o.left}; width:${o.w}; height:${o.h}; border-radius:${o.radius || "50%"}; background:${o.color}; ${blurStyle}"></div>`;
  }).join("");

  let ringsHtml = "";
  if (cfg.rings) {
    const ringOpacity = cfg.rings.faint ? 0.28 : 0.55;
    const ringW = Math.round(cfg.rings.faint ? size * 1.35 : size * 1.55);
    const ringH = Math.round(cfg.rings.faint ? size * 0.18 : size * 0.30);
    const borderW = cfg.rings.faint ? 4 : 10;
    ringsHtml = `<div style="position:absolute; top:${offset + size / 2}px; right:${offset + size / 2}px; width:${ringW}px; height:${ringH}px; transform:translate(50%,-50%) rotate(-8deg); border-radius:50%; border:${borderW}px solid rgba(220,205,170,${ringOpacity}); box-shadow:0 0 30px rgba(220,205,170,${ringOpacity * 0.5});"></div>`;
  }

  return `
    <div style="position:absolute; top:${offset - 60}px; right:${offset - 60}px; width:${size + 120}px; height:${size + 120}px; border-radius:50%; box-shadow:0 0 160px 60px ${cfg.glowColor};"></div>
    ${ringsHtml}
    <div style="position:absolute; top:${offset}px; right:${offset}px; width:${size}px; height:${size}px; border-radius:50%; background:${cfg.sphereBackground}; box-shadow:${boxShadow}; filter:${filter}; opacity:0.92; overflow:hidden;">
      ${overlaysHtml}
    </div>
    <div style="position:absolute; top:${offset}px; right:${offset}px; width:${size}px; height:${size}px; border-radius:50%; background:radial-gradient(circle at 35% 30%, rgba(255,255,255,0.14), rgba(0,0,0,0) 55%);"></div>
  `;
}

function applyPlanetScene(planetKey) {
  const cfg = PLANET_SCENES[planetKey];
  if (!cfg) return;
  const scene = document.getElementById("planet-scene");
  scene.innerHTML = buildPlanetSceneHTML(planetKey);
  messagesEl.style.background = `radial-gradient(ellipse 900px 700px at 78% 18%, ${cfg.ambientTint} 0%, rgba(0, 0, 0, 0) 60%), #000000`;
  scene.classList.add("active");
}

function clearPlanetScene() {
  const scene = document.getElementById("planet-scene");
  scene.classList.remove("active");
  messagesEl.style.background = "";
}

const GREETINGS = [
  "What shall we explore today?", "What are we building today?", "Where should we begin?",
  "What's our next mission?", "Where are we headed today?", "What mystery shall we solve?",
  "What will we discover today?", "What challenge awaits?", "Where does your curiosity lead?",
  "What's the destination?", "What shall we create?", "What's your next breakthrough?",
  "What idea are we launching?", "What universe are we exploring?", "Which path should we chart?",
  "What are you curious about?", "What deserves a closer look?", "What's your next adventure?",
  "What can we unlock today?", "Where shall we venture?", "What's orbiting your mind?",
  "Which idea should we ignite?", "What are we discovering next?", "What project are we launching?",
  "What question needs an answer?", "What's your next big idea?", "Which galaxy are we visiting today?",
  "What shall we investigate?", "What can I help uncover?", "What deserves exploration?",
  "What should we navigate?", "What knowledge are we chasing?", "Where should we set our course?",
  "Which challenge should we tackle?", "What's beyond the horizon?", "What's waiting to be discovered?",
  "What should we decode?", "What shall we map today?", "What possibilities should we explore?",
  "What's your next destination?", "Which problem shall we solve?", "What shall we illuminate?",
  "What's hidden beneath the surface?", "Where will curiosity take us?", "What should we analyze?",
  "Which star are we aiming for?", "What inspires you today?", "What idea deserves attention?",
  "What's your next experiment?", "What shall we uncover together?", "Which mission comes first?",
  "What's your launch plan?", "What should we engineer?", "What's the next objective?",
  "Which route should we take?", "What knowledge are we seeking?", "Where should our journey begin?",
  "What challenge excites you?", "Which frontier shall we cross?", "What's your next discovery?",
  "What should we invent?", "What puzzle are we solving?", "What deserves another perspective?",
  "What would you like to understand?", "What's waiting beyond the next question?", "Where should our ideas travel?",
  "What should we investigate first?", "What should we build together?", "What's worth exploring today?",
  "What can we accomplish together?", "Which concept should we dive into?", "What's your next creation?",
  "What should we imagine?", "What should we bring to life?", "What deserves a deeper look?",
  "What's the next signal?", "Which star should we follow?", "What mission are we preparing for?",
  "What question sparks your curiosity?", "What's calling for attention?", "What should we optimize?",
  "What should we transform?", "What's the next milestone?", "Which dream should we build?",
  "What should we solve first?", "What's your next launch?", "What should we prototype?",
  "What are we discovering together?", "What's waiting in the unknown?", "Where should inspiration lead us?",
  "What challenge are we accepting?", "What should we decode next?", "Which idea deserves liftoff?",
  "What's the next chapter?", "Where should innovation begin?", "What can we accomplish today?",
  "Which mystery intrigues you most?", "What should we search for?", "What should we rethink?",
  "What are we aiming for today?", "Where shall curiosity take us next?", "What future shall we build?",
];

const THINKING_PHRASES = [
  "Thinking...", "Analyzing...", "Planning response...", "Reasoning...",
  "Understanding request...", "Locking in...", "Finding a teacher...", "Googling...",
  "Asking a teacher...", "Sleeping...", "Asking ChatGPT... 👀", "Borrowing Claude's neurons...",
  "Convincing the electrons...", "Googling respectfully...", "Speedrunning intelligence...",
  "Realizing this could've been a Google search...",
];

function randomThinkingPhrase() {
  return THINKING_PHRASES[Math.floor(Math.random() * THINKING_PHRASES.length)];
}

const CHATS_KEY = "nova.chats";
const ACTIVE_CHAT_KEY = "nova.activeChatId";

let history = [];
let messageList = null;
let chats = loadChats();
let activeChatId = localStorage.getItem(ACTIVE_CHAT_KEY);

let currentView = "nebula";
let healthHistory = [];
let healthMessageList = null;
// Kept across a whole meal-logging exchange (not cleared after the first send) so
// every follow-up request still carries the photo — otherwise the model loses the
// image once a clarifying question moves the conversation to text-only replies.
let healthImageFile = null;

function loadChats() {
  try {
    return JSON.parse(localStorage.getItem(CHATS_KEY)) || [];
  } catch {
    return [];
  }
}

function saveChats() {
  localStorage.setItem(CHATS_KEY, JSON.stringify(chats));
}

function setActiveChatId(id) {
  activeChatId = id;
  if (id) {
    localStorage.setItem(ACTIVE_CHAT_KEY, id);
  } else {
    localStorage.removeItem(ACTIVE_CHAT_KEY);
  }
}

function chatTitleFrom(messages) {
  const firstUser = messages.find(m => m.role === "user");
  if (!firstUser) return "New chat";
  return firstUser.content.length > 40 ? firstUser.content.slice(0, 40) + "…" : firstUser.content;
}

function persistCurrentChat() {
  if (!activeChatId) {
    setActiveChatId(crypto.randomUUID());
    chats.push({ id: activeChatId, title: "New chat", messages: [], updatedAt: 0 });
  }
  const chat = chats.find(c => c.id === activeChatId);
  chat.messages = history;
  chat.title = chatTitleFrom(history);
  chat.updatedAt = Date.now();
  saveChats();
  renderChatList();
}

let confirmingDeleteId = null;
let confirmingDeleteTimeout = null;

function deleteChat(id) {
  chats = chats.filter(c => c.id !== id);
  saveChats();
  if (id === activeChatId) {
    history = [];
    setActiveChatId(null);
    clearMessageArea();
    showEmptyState();
  }
  renderChatList();
}

function renderChatList() {
  chatListEl.innerHTML = "";
  const sorted = [...chats].sort((a, b) => b.updatedAt - a.updatedAt);
  for (const chat of sorted) {
    const row = document.createElement("div");
    row.className = "chat-item-row";

    const btn = document.createElement("button");
    btn.className = "chat-item" + (chat.id === activeChatId ? " active" : "");
    btn.textContent = chat.title;
    btn.addEventListener("click", () => switchToChat(chat.id));

    const isConfirming = chat.id === confirmingDeleteId;
    const del = document.createElement("button");
    del.className = "chat-delete-btn" + (isConfirming ? " confirming" : "");
    del.setAttribute("aria-label", isConfirming ? "Confirm delete" : "Delete chat");
    del.innerHTML = isConfirming
      ? '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'
      : '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>';

    del.addEventListener("click", (e) => {
      e.stopPropagation();
      clearTimeout(confirmingDeleteTimeout);
      if (confirmingDeleteId === chat.id) {
        confirmingDeleteId = null;
        deleteChat(chat.id);
      } else {
        confirmingDeleteId = chat.id;
        renderChatList();
        confirmingDeleteTimeout = setTimeout(() => {
          confirmingDeleteId = null;
          renderChatList();
        }, 3000);
      }
    });

    row.appendChild(btn);
    row.appendChild(del);
    chatListEl.appendChild(row);
  }
}

function clearMessageArea() {
  if (messageList) {
    messageList.remove();
    messageList = null;
  }
  const existingEmpty = document.getElementById("empty-state");
  if (existingEmpty) existingEmpty.remove();
}

function switchToChat(id) {
  if (id === activeChatId) return;
  setActiveChatId(id);
  const chat = chats.find(c => c.id === id);
  history = chat ? chat.messages.slice() : [];

  clearMessageArea();
  if (history.length === 0) {
    showEmptyState();
  } else {
    for (const m of history) {
      addMessage(m.role, m.content, m.sources, m.webSources);
    }
  }
  renderChatList();
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function renderMarkdown(str) {
  // Escape first so the raw text can never introduce HTML; the replacements
  // below only ever wrap already-escaped text in tags, never insert user input as markup.
  let html = escapeHtml(str);
  html = html.replace(/```([\s\S]+?)```/g, (_, code) => `<code class="block">${code}</code>`);
  html = html.replace(/`([^`]+?)`/g, "<code>$1</code>");
  html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
  html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
  html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");
  html = html.replace(/\*\*([^*]+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/(^|\s)\*([^*]+?)\*(?=\s|$)/g, "$1<em>$2</em>");
  return html;
}

const FEATURED_GREETING = "Every great discovery starts with a question.";

const AFTERNOON_GREETINGS = [
  "Good afternoon. What's calling for attention?",
  "Which idea should we dive into?",
  "What's today's next discovery?",
  "What's worth exploring this afternoon?",
  "Ready to solve something interesting?",
  "Where should we focus next?",
  "What's keeping your mind busy?",
  "Which concept should we unlock?",
  "Let's keep the momentum going.",
  "What would you like to understand?",
  "What's the next mission?",
  "What deserves a closer look?",
];

function isIstAfternoon() {
  const istHour = parseInt(
    new Intl.DateTimeFormat("en-US", { timeZone: "Asia/Kolkata", hour: "numeric", hour12: false }).format(new Date()),
    10
  );
  return istHour >= 13 && istHour < 16;
}

function setGreeting() {
  const pool = isIstAfternoon() ? AFTERNOON_GREETINGS : GREETINGS;
  greetingEl.textContent = Math.random() < 0.3
    ? FEATURED_GREETING
    : pool[Math.floor(Math.random() * pool.length)];
}

function renderSuggestions() {
  suggestionsEl.innerHTML = "";
  for (const s of SUGGESTIONS) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = s;
    btn.addEventListener("click", () => {
      input.value = s;
      input.dispatchEvent(new Event("input"));
      input.focus();
    });
    suggestionsEl.appendChild(btn);
  }
}

function showEmptyState() {
  if (messageList) {
    messageList.remove();
    messageList = null;
  }
  if (!document.getElementById("empty-state")) {
    setGreeting();
    messagesScrollEl.appendChild(emptyState);
  }
}

function ensureMessageList() {
  if (!messageList) {
    const existingEmpty = document.getElementById("empty-state");
    if (existingEmpty) existingEmpty.remove();
    messageList = document.createElement("div");
    messageList.className = "message-list";
    messagesScrollEl.appendChild(messageList);
  }
  return messageList;
}

function appendSourcesToBubble(bubble, sources, webSources) {
  if (sources && sources.length) {
    const src = document.createElement("span");
    src.className = "sources";
    src.textContent = `Notes: ${sources.join(", ")}`;
    bubble.appendChild(src);
  }
  if (webSources && webSources.length) {
    const web = document.createElement("span");
    web.className = "sources";
    web.innerHTML = "Web: " + webSources
      .map(s => `<a href="${escapeHtml(s.url)}" target="_blank" rel="noopener">${escapeHtml(s.title || s.url)}</a>`)
      .join(", ");
    bubble.appendChild(web);
  }
}

function showHealthEmptyState() {
  if (healthMessageList) {
    healthMessageList.remove();
    healthMessageList = null;
  }
  if (!document.getElementById("health-empty-state")) {
    healthMessagesScrollEl.appendChild(healthEmptyState);
  }
}

function ensureHealthMessageList() {
  if (!healthMessageList) {
    const existingEmpty = document.getElementById("health-empty-state");
    if (existingEmpty) existingEmpty.remove();
    healthMessageList = document.createElement("div");
    healthMessageList.className = "message-list";
    healthMessagesScrollEl.appendChild(healthMessageList);
  }
  return healthMessageList;
}

function addHealthMessage(role, text, imageDataUrl) {
  const list = ensureHealthMessageList();

  const row = document.createElement("div");
  row.className = `row ${role}`;

  if (role !== "user") {
    const avatar = document.createElement("div");
    avatar.className = "row-avatar";
    avatar.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="#facc15"><path d="M12 1.5c.6 4.4 2.1 6.9 4.5 8.9 2.4 1.9 5 2.7 6 3.1-1 .4-3.6 1.2-6 3.1-2.4 2-3.9 4.5-4.5 8.9-.6-4.4-2.1-6.9-4.5-8.9-2.4-1.9-5-2.7-6-3.1 1-.4 3.6-1.2 6-3.1 2.4-2 3.9-4.5 4.5-8.9z"/></svg>';
    row.appendChild(avatar);
  }

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  if (imageDataUrl) {
    const img = document.createElement("img");
    img.className = "health-photo-thumb";
    img.src = imageDataUrl;
    bubble.appendChild(img);
  }
  if (text) {
    const textEl = document.createElement("span");
    textEl.innerHTML = renderMarkdown(text);
    bubble.appendChild(textEl);
  }

  row.appendChild(bubble);
  list.appendChild(row);
  healthMessagesScrollEl.scrollTop = healthMessagesScrollEl.scrollHeight;
  return row;
}

function beginHealthStreamingMessage() {
  const list = ensureHealthMessageList();

  const row = document.createElement("div");
  row.className = "row assistant";

  const avatar = document.createElement("div");
  avatar.className = "row-avatar";
  avatar.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="#facc15"><path d="M12 1.5c.6 4.4 2.1 6.9 4.5 8.9 2.4 1.9 5 2.7 6 3.1-1 .4-3.6 1.2-6 3.1-2.4 2-3.9 4.5-4.5 8.9-.6-4.4-2.1-6.9-4.5-8.9-2.4-1.9-5-2.7-6-3.1 1-.4 3.6-1.2 6-3.1 2.4-2 3.9-4.5 4.5-8.9z"/></svg>';
  row.appendChild(avatar);

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  row.appendChild(bubble);

  list.appendChild(row);
  healthMessagesScrollEl.scrollTop = healthMessagesScrollEl.scrollHeight;
  return bubble;
}

async function loadHealthLog() {
  try {
    const res = await fetch("/api/health/log");
    const data = await res.json();
    healthTodayTotal.textContent = `Today: ${Math.round(data.today_total_calories)} kcal`;

    healthLogList.innerHTML = "";
    for (const entry of [...data.entries].reverse()) {
      const item = document.createElement("div");
      item.className = "health-log-item";
      const time = new Date(entry.timestamp).toLocaleString([], { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
      item.innerHTML = `
        <div class="health-log-item-desc">${escapeHtml(entry.description)}</div>
        <div class="health-log-item-meta">${Math.round(entry.calories)} kcal · ${escapeHtml(time)}</div>
      `;
      healthLogList.appendChild(item);
    }
  } catch (err) {
    // Log sidebar is a nice-to-have; a failed fetch shouldn't block the rest of the view.
  }
}

function clearHealthPreview() {
  healthImageFile = null;
  healthPreview.hidden = true;
  healthPreview.innerHTML = "";
  healthPhotoBtn.classList.remove("has-photo");
  healthPhotoInput.value = "";
}

function updateHealthSendState() {
  const hasText = healthInput.value.trim().length > 0;
  healthSendBtn.disabled = !hasText && !healthImageFile;
  healthSendBtn.classList.toggle("ready", hasText || !!healthImageFile);
}

healthPhotoBtn.addEventListener("click", () => healthPhotoInput.click());

healthPhotoInput.addEventListener("change", () => {
  const file = healthPhotoInput.files[0];
  if (!file) return;
  healthImageFile = file;
  healthPhotoBtn.classList.add("has-photo");

  const reader = new FileReader();
  reader.onload = () => {
    healthPreview.hidden = false;
    healthPreview.innerHTML = `
      <img src="${reader.result}">
      <span>${escapeHtml(file.name)}</span>
      <button type="button" id="health-preview-remove">Remove</button>
    `;
    document.getElementById("health-preview-remove").addEventListener("click", clearHealthPreview);
  };
  reader.readAsDataURL(file);
  updateHealthSendState();
});

healthInput.addEventListener("input", () => {
  updateHealthSendState();
  healthInput.style.height = "auto";
  healthInput.style.height = Math.min(healthInput.scrollHeight, 160) + "px";
});

healthInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendHealthMessage();
  }
});

healthSendBtn.addEventListener("click", sendHealthMessage);

async function sendHealthMessage() {
  const message = healthInput.value.trim();
  const imageFile = healthImageFile;
  if (!message && !imageFile) return;

  let imageDataUrl = null;
  if (imageFile) {
    imageDataUrl = await new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.readAsDataURL(imageFile);
    });
  }
  addHealthMessage("user", message, imageDataUrl);

  healthInput.value = "";
  healthInput.style.height = "auto";
  healthPreview.hidden = true;
  healthSendBtn.disabled = true;
  healthSendBtn.classList.remove("ready");

  const priorHistory = healthHistory.slice();
  healthHistory.push({ role: "user", content: message || "[uploaded a photo]" });

  const formData = new FormData();
  formData.append("message", message);
  formData.append("history", JSON.stringify(priorHistory));
  if (imageFile) formData.append("image", imageFile);

  const bubble = beginHealthStreamingMessage();
  let fullText = "";
  let logged = false;

  try {
    const res = await fetch("/api/health/analyze", { method: "POST", body: formData });
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let newlineIdx;
      while ((newlineIdx = buffer.indexOf("\n")) !== -1) {
        const line = buffer.slice(0, newlineIdx);
        buffer = buffer.slice(newlineIdx + 1);
        if (!line.trim()) continue;

        const chunk = JSON.parse(line);
        if (chunk.token) {
          fullText += chunk.token;
          bubble.innerHTML = renderMarkdown(fullText);
          healthMessagesScrollEl.scrollTop = healthMessagesScrollEl.scrollHeight;
        } else if (chunk.done) {
          logged = chunk.logged;
        }
      }
    }

    healthHistory.push({ role: "assistant", content: fullText });

    if (logged) {
      // Meal finalized — reset for the next one, including the carried-along photo.
      clearHealthPreview();
      healthHistory = [];
      loadHealthLog();
    }
  } catch (err) {
    bubble.textContent = "Something went wrong reaching the server.";
  } finally {
    healthInput.focus();
  }
}

function addMessage(role, text, sources, webSources) {
  const list = ensureMessageList();

  const row = document.createElement("div");
  row.className = `row ${role}`;

  if (role !== "user") {
    const avatar = document.createElement("div");
    avatar.className = "row-avatar";
    avatar.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="#facc15"><path d="M12 1.5c.6 4.4 2.1 6.9 4.5 8.9 2.4 1.9 5 2.7 6 3.1-1 .4-3.6 1.2-6 3.1-2.4 2-3.9 4.5-4.5 8.9-.6-4.4-2.1-6.9-4.5-8.9-2.4-1.9-5-2.7-6-3.1 1-.4 3.6-1.2 6-3.1 2.4-2 3.9-4.5 4.5-8.9z"/></svg>';
    row.appendChild(avatar);
  }

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = renderMarkdown(text);
  appendSourcesToBubble(bubble, sources, webSources);

  row.appendChild(bubble);
  list.appendChild(row);
  messagesScrollEl.scrollTop = messagesScrollEl.scrollHeight;
  return row;
}

function beginStreamingMessage() {
  const list = ensureMessageList();

  const row = document.createElement("div");
  row.className = "row assistant";

  const avatar = document.createElement("div");
  avatar.className = "row-avatar";
  avatar.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="#facc15"><path d="M12 1.5c.6 4.4 2.1 6.9 4.5 8.9 2.4 1.9 5 2.7 6 3.1-1 .4-3.6 1.2-6 3.1-2.4 2-3.9 4.5-4.5 8.9-.6-4.4-2.1-6.9-4.5-8.9-2.4-1.9-5-2.7-6-3.1 1-.4 3.6-1.2 6-3.1 2.4-2 3.9-4.5 4.5-8.9z"/></svg>';
  row.appendChild(avatar);

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  row.appendChild(bubble);

  list.appendChild(row);
  messagesScrollEl.scrollTop = messagesScrollEl.scrollHeight;
  return bubble;
}

function autoGrow() {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 160) + "px";
}

let stars = [];
let asteroids = [];
let starfieldRAF = null;
let starfieldActive = false;
let activePlanet = null;

function resizeStarfield() {
  starfieldCanvas.width = messagesEl.clientWidth;
  starfieldCanvas.height = messagesEl.clientHeight;
}

function initStars(count = 220) {
  stars = Array.from({ length: count }, () => ({
    x: Math.random() * starfieldCanvas.width,
    y: Math.random() * starfieldCanvas.height,
    r: Math.random() * 1.4 + 0.3,
    speed: Math.random() * 0.4 + 0.08,
    twinklePhase: Math.random() * Math.PI * 2,
  }));
}

function spawnAsteroid() {
  return {
    x: Math.random() * starfieldCanvas.width * 0.6,
    y: -20 - Math.random() * starfieldCanvas.height * 0.5,
    vx: 1 + Math.random() * 0.8,
    vy: 1.8 + Math.random() * 1.4,
    len: 16 + Math.random() * 14,
    size: 1.3 + Math.random() * 1,
  };
}

function initAsteroids(count = 3) {
  asteroids = Array.from({ length: count }, spawnAsteroid);
}

function updateAndDrawAsteroid(a, speedMultiplier) {
  a.x += a.vx * speedMultiplier;
  a.y += a.vy * speedMultiplier;
  if (a.y > starfieldCanvas.height + 40 || a.x > starfieldCanvas.width + 40) {
    Object.assign(a, spawnAsteroid());
  }

  const tailX = a.x - a.vx * a.len;
  const tailY = a.y - a.vy * a.len;
  const trail = starCtx.createLinearGradient(tailX, tailY, a.x, a.y);
  trail.addColorStop(0, "rgba(255, 100, 0, 0)");
  trail.addColorStop(0.6, "rgba(255, 140, 0, 0.55)");
  trail.addColorStop(1, "rgba(255, 230, 180, 0.95)");
  starCtx.strokeStyle = trail;
  starCtx.lineWidth = a.size;
  starCtx.lineCap = "round";
  starCtx.beginPath();
  starCtx.moveTo(tailX, tailY);
  starCtx.lineTo(a.x, a.y);
  starCtx.stroke();

  starCtx.shadowColor = "rgba(255, 120, 0, 0.9)";
  starCtx.shadowBlur = 8;
  starCtx.beginPath();
  starCtx.arc(a.x, a.y, a.size, 0, Math.PI * 2);
  starCtx.fillStyle = "rgba(255, 255, 255, 1)";
  starCtx.fill();
  starCtx.shadowBlur = 0;
}

function drawAsteroids() {
  for (const a of asteroids) updateAndDrawAsteroid(a, 1);
}

let iss = null;

function spawnISS() {
  return {
    x: -60,
    baseY: starfieldCanvas.height * (0.12 + Math.random() * 0.5),
    vx: 0.3 + Math.random() * 0.15,
    arcAmplitude: 10 + Math.random() * 12,
    arcPhase: Math.random() * Math.PI * 2,
  };
}

function initISS() {
  iss = spawnISS();
}

function roundRectPath(x, y, w, h, r) {
  starCtx.beginPath();
  starCtx.moveTo(x + r, y);
  starCtx.arcTo(x + w, y, x + w, y + h, r);
  starCtx.arcTo(x + w, y + h, x, y + h, r);
  starCtx.arcTo(x, y + h, x, y, r);
  starCtx.arcTo(x, y, x + w, y, r);
  starCtx.closePath();
}

function drawISSPanel(startX, direction) {
  const panelW = 13;
  const panelH = 6;
  const x0 = direction < 0 ? startX - panelW : startX;

  const grad = starCtx.createLinearGradient(x0, 0, x0 + panelW, 0);
  if (direction < 0) {
    grad.addColorStop(0, "rgba(45, 65, 130, 0.9)");
    grad.addColorStop(1, "rgba(90, 125, 205, 0.95)");
  } else {
    grad.addColorStop(0, "rgba(90, 125, 205, 0.95)");
    grad.addColorStop(1, "rgba(45, 65, 130, 0.9)");
  }
  starCtx.fillStyle = grad;
  roundRectPath(x0, -panelH / 2, panelW, panelH, 1);
  starCtx.fill();

  starCtx.strokeStyle = "rgba(190, 205, 235, 0.5)";
  starCtx.lineWidth = 0.5;
  for (let i = 1; i < 4; i++) {
    const lx = x0 + (panelW / 4) * i;
    starCtx.beginPath();
    starCtx.moveTo(lx, -panelH / 2 + 0.5);
    starCtx.lineTo(lx, panelH / 2 - 0.5);
    starCtx.stroke();
  }
}

function drawISS() {
  if (!iss) return;
  iss.x += iss.vx;
  const y = iss.baseY + Math.sin(iss.x / 260 + iss.arcPhase) * iss.arcAmplitude;
  if (iss.x > starfieldCanvas.width + 60) {
    iss = spawnISS();
    return;
  }

  const gap = 3.5;

  starCtx.save();
  starCtx.translate(iss.x, y);
  starCtx.shadowColor = "rgba(215, 228, 255, 0.8)";
  starCtx.shadowBlur = 5;

  // Truss spanning the full structure, drawn first so panels/module sit on top.
  starCtx.strokeStyle = "rgba(200, 212, 232, 0.75)";
  starCtx.lineWidth = 1;
  starCtx.beginPath();
  starCtx.moveTo(-(gap + 13), 0);
  starCtx.lineTo(gap + 13, 0);
  starCtx.stroke();

  drawISSPanel(-gap, -1);
  drawISSPanel(gap, 1);

  starCtx.fillStyle = "rgba(238, 239, 243, 0.98)";
  roundRectPath(-gap, -2.1, gap * 2, 4.2, 1.3);
  starCtx.fill();

  starCtx.shadowBlur = 0;
  starCtx.restore();
}

function updateAndDrawStar(star, time, twinkleSpeedMultiplier) {
  star.y += star.speed;
  if (star.y > starfieldCanvas.height) {
    star.y = 0;
    star.x = Math.random() * starfieldCanvas.width;
  }
  const twinkle = 0.5 + 0.5 * Math.sin((time / 500) * twinkleSpeedMultiplier + star.twinklePhase);
  starCtx.beginPath();
  starCtx.arc(star.x, star.y, star.r, 0, Math.PI * 2);
  starCtx.fillStyle = `rgba(255, 255, 255, ${0.25 + 0.75 * twinkle})`;
  starCtx.fill();
}

function drawStars(time) {
  starCtx.clearRect(0, 0, starfieldCanvas.width, starfieldCanvas.height);
  for (const star of stars) updateAndDrawStar(star, time, 1);
  drawAsteroids();
  drawISS();
  starfieldRAF = requestAnimationFrame(drawStars);
}

function startStarfield() {
  resizeStarfield();
  initStars();
  initAsteroids();
  initISS();
  starfieldCanvas.classList.add("active");
  starfieldActive = true;
  moonIcon.style.display = "none";
  if (!starfieldRAF) starfieldRAF = requestAnimationFrame(drawStars);
}

function startPlanetReveal(planetKey) {
  activePlanet = planetKey;
  applyPlanetScene(planetKey);
}

function switchToPlanet(planetKey) {
  const wasActive = !!activePlanet;
  activePlanet = null;
  clearPlanetScene();
  // Let the fade-out transition (see #planet-scene.active in style.css) finish
  // before swapping content and fading the new planet in, rather than replacing
  // instantly under the old one.
  setTimeout(() => startPlanetReveal(planetKey), wasActive ? 800 : 0);
}

function startStarfieldWithTransition(planetKey = null) {
  resizeStarfield();
  initStars();
  initAsteroids();
  initISS();
  starfieldCanvas.classList.add("active");
  starfieldActive = true;
  moonIcon.style.display = "none";

  const logoEl = document.querySelector(".empty-logo");
  let originX = starfieldCanvas.width / 2;
  let originY = starfieldCanvas.height / 2;
  if (logoEl) {
    const canvasRect = starfieldCanvas.getBoundingClientRect();
    const logoRect = logoEl.getBoundingClientRect();
    originX = logoRect.left + logoRect.width / 2 - canvasRect.left;
    originY = logoRect.top + logoRect.height / 2 - canvasRect.top;

    logoEl.style.transition = "opacity 0.4s ease, transform 0.4s ease";
    logoEl.style.transform = "scale(0.15)";
    logoEl.style.opacity = "0";
  }

  const burstParticles = stars.map(s => ({ finalX: s.x, finalY: s.y, r: s.r }));
  const burstDuration = 900;
  const burstStart = performance.now();

  function burstFrame(now) {
    const t = Math.min(1, (now - burstStart) / burstDuration);
    const eased = 1 - Math.pow(1 - t, 3);

    starCtx.clearRect(0, 0, starfieldCanvas.width, starfieldCanvas.height);

    for (const p of burstParticles) {
      const x = originX + (p.finalX - originX) * eased;
      const y = originY + (p.finalY - originY) * eased;
      starCtx.beginPath();
      starCtx.arc(x, y, p.r, 0, Math.PI * 2);
      starCtx.fillStyle = `rgba(255, 255, 255, ${0.3 + 0.7 * eased})`;
      starCtx.fill();
    }

    const flashAlpha = Math.max(0, 1 - t * 2);
    if (flashAlpha > 0) {
      const grad = starCtx.createRadialGradient(originX, originY, 0, originX, originY, 90);
      grad.addColorStop(0, `rgba(255, 255, 255, ${flashAlpha * 0.85})`);
      grad.addColorStop(1, "rgba(255, 255, 255, 0)");
      starCtx.fillStyle = grad;
      starCtx.fillRect(0, 0, starfieldCanvas.width, starfieldCanvas.height);
    }

    if (t < 1) {
      starfieldRAF = requestAnimationFrame(burstFrame);
    } else {
      if (logoEl) {
        logoEl.style.transform = "";
        logoEl.style.opacity = "1";
      }
      if (planetKey) startPlanetReveal(planetKey);
      starfieldRAF = requestAnimationFrame(drawStars);
    }
  }
  starfieldRAF = requestAnimationFrame(burstFrame);
}

function stopStarfield() {
  starfieldActive = false;
  activePlanet = null;
  clearPlanetScene();
  starfieldCanvas.classList.remove("active");
  moonIcon.style.display = "";
  const logoEl = document.querySelector(".empty-logo");
  if (logoEl) {
    logoEl.style.transition = "";
    logoEl.style.transform = "";
    logoEl.style.opacity = "1";
  }
  if (starfieldRAF) {
    cancelAnimationFrame(starfieldRAF);
    starfieldRAF = null;
  }
}

function makeExplosionParticle(x, y, colorPrefix) {
  const angle = Math.random() * Math.PI * 2;
  const speed = 2 + Math.random() * 6;
  return {
    x, y,
    vx: Math.cos(angle) * speed,
    vy: Math.sin(angle) * speed,
    life: 1,
    decay: 0.012 + Math.random() * 0.02,
    r: 1 + Math.random() * 2,
    colorPrefix,
  };
}

const NOVA_LOGO_PATH = new Path2D(
  "M12 1.5c.6 4.4 2.1 6.9 4.5 8.9 2.4 1.9 5 2.7 6 3.1-1 .4-3.6 1.2-6 3.1" +
  "-2.4 2-3.9 4.5-4.5 8.9-.6-4.4-2.1-6.9-4.5-8.9-2.4-1.9-5-2.7-6-3.1" +
  "1-.4 3.6-1.2 6-3.1 2.4-2 3.9-4.5 4.5-8.9z"
);

function drawNovaLogo(cx, cy, progress) {
  if (progress <= 0) return;
  const scale = 2.4 * progress;
  starCtx.save();
  starCtx.translate(cx, cy);
  starCtx.scale(scale, scale);
  starCtx.translate(-12, -12);
  starCtx.shadowColor = "rgba(250, 204, 21, 0.9)";
  starCtx.shadowBlur = 20 / scale;
  starCtx.fillStyle = `rgba(250, 204, 21, ${Math.min(1, progress * 1.3)})`;
  starCtx.fill(NOVA_LOGO_PATH);
  starCtx.restore();
}

function triggerSupernova() {
  if (starfieldRAF) {
    cancelAnimationFrame(starfieldRAF);
    starfieldRAF = null;
  }

  // /supernova should work whether or not /nova was run first — start the
  // starfield here (no logo-implosion intro, that's specific to /nova) if it
  // isn't already active.
  if (!starfieldActive) {
    resizeStarfield();
    initStars();
    initAsteroids();
    initISS();
    starfieldCanvas.classList.add("active");
    starfieldActive = true;
    moonIcon.style.display = "none";
  }

  // Mid-chat, the starfield renders behind #messages-scroll (lower z-index),
  // so fade the chat out to reveal it instead of the empty-state logo.
  const hasMessages = messagesScrollEl.children.length > 0;
  const fadeTarget = hasMessages ? messagesScrollEl : document.querySelector(".empty-logo");
  if (fadeTarget) {
    fadeTarget.style.transition = "opacity 0.8s ease";
    fadeTarget.style.opacity = "0";
  }

  const rampDuration = 3000;
  const rampStart = performance.now();

  function rampFrame(now) {
    const t = Math.min(1, (now - rampStart) / rampDuration);
    const twinkleSpeedMultiplier = 1 + t * 7;
    const asteroidSpeedMultiplier = 1 + t * 4;

    starCtx.clearRect(0, 0, starfieldCanvas.width, starfieldCanvas.height);
    for (const star of stars) updateAndDrawStar(star, now, twinkleSpeedMultiplier);
    for (const a of asteroids) updateAndDrawAsteroid(a, asteroidSpeedMultiplier);

    if (t < 1) {
      starfieldRAF = requestAnimationFrame(rampFrame);
    } else {
      startExplodePhase();
    }
  }
  starfieldRAF = requestAnimationFrame(rampFrame);

  function startExplodePhase() {
    const particles = [
      ...stars.map(s => makeExplosionParticle(s.x, s.y, "rgba(255, 255, 255, ")),
      ...asteroids.map(a => makeExplosionParticle(a.x, a.y, "rgba(255, 160, 60, ")),
    ];

    const explodeDuration = 1000;
    const explodeStart = performance.now();

    function explodeFrame(now) {
      const t = Math.min(1, (now - explodeStart) / explodeDuration);
      starCtx.clearRect(0, 0, starfieldCanvas.width, starfieldCanvas.height);

      const flashAlpha = Math.max(0, 1 - t * 3);
      if (flashAlpha > 0) {
        starCtx.fillStyle = `rgba(255, 255, 255, ${flashAlpha * 0.5})`;
        starCtx.fillRect(0, 0, starfieldCanvas.width, starfieldCanvas.height);
      }

      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        starCtx.beginPath();
        starCtx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        starCtx.fillStyle = `${p.colorPrefix}${1 - t})`;
        starCtx.fill();
      }

      if (t < 1) {
        starfieldRAF = requestAnimationFrame(explodeFrame);
      } else {
        startMergePhase(particles);
      }
    }
    starfieldRAF = requestAnimationFrame(explodeFrame);
  }

  function startMergePhase(particles) {
    const cx = starfieldCanvas.width / 2;
    const cy = starfieldCanvas.height / 2;
    for (const p of particles) {
      p.startX = p.x;
      p.startY = p.y;
    }

    const mergeDuration = 1500;
    const mergeStart = performance.now();

    function mergeFrame(now) {
      const t = Math.min(1, (now - mergeStart) / mergeDuration);
      const eased = 1 - Math.pow(1 - t, 2);

      starCtx.clearRect(0, 0, starfieldCanvas.width, starfieldCanvas.height);
      for (const p of particles) {
        const x = p.startX + (cx - p.startX) * eased;
        const y = p.startY + (cy - p.startY) * eased;
        starCtx.beginPath();
        starCtx.arc(x, y, p.r * (1 - eased * 0.5), 0, Math.PI * 2);
        starCtx.fillStyle = `${p.colorPrefix}${Math.max(0.15, 1 - eased * 0.6)})`;
        starCtx.fill();
      }

      if (fadeTarget) {
        // Hold off appearing until the particles have mostly converged, then fade
        // in slowly over the remaining time — a staggered reveal, not a linear one.
        fadeTarget.style.transition = "none";
        fadeTarget.style.opacity = String(Math.max(0, (t - 0.3) / 0.7));
      } else {
        drawNovaLogo(cx, cy, eased);
      }

      if (t < 1) {
        starfieldRAF = requestAnimationFrame(mergeFrame);
      } else {
        if (fadeTarget) {
          fadeTarget.style.opacity = "1";
          fadeTarget.style.transition = "";
        }
        setTimeout(() => {
          starCtx.clearRect(0, 0, starfieldCanvas.width, starfieldCanvas.height);
          stopStarfield();
        }, 400);
      }
    }
    starfieldRAF = requestAnimationFrame(mergeFrame);
  }
}

window.addEventListener("resize", () => {
  if (starfieldActive) resizeStarfield();
});

async function sendMessage() {
  const message = input.value.trim();
  if (!message) return;

  if (message.toLowerCase() === "/supernova") {
    input.value = "";
    autoGrow();
    sendBtn.disabled = true;
    sendBtn.classList.remove("ready");
    triggerSupernova();
    return;
  }

  const novaMatch = message.match(/^\/nova(?:\s+(\w+))?$/i);
  if (novaMatch) {
    input.value = "";
    autoGrow();
    sendBtn.disabled = true;
    sendBtn.classList.remove("ready");

    const requestedPlanet = novaMatch[1] ? novaMatch[1].toLowerCase() : null;
    const validPlanet = requestedPlanet && PLANETS[requestedPlanet] ? requestedPlanet : null;

    if (!starfieldActive) {
      startStarfieldWithTransition(validPlanet);
    } else if (validPlanet && validPlanet !== activePlanet) {
      switchToPlanet(validPlanet);
    } else {
      stopStarfield();
    }
    return;
  }

  addMessage("user", message);
  input.value = "";
  autoGrow();
  sendBtn.disabled = true;
  sendBtn.classList.remove("ready");

  const priorHistory = history.slice();
  history.push({ role: "user", content: message });
  persistCurrentChat();

  const pending = addMessage("assistant pending", randomThinkingPhrase());

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history: priorHistory }),
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let fullText = "";
    let bubble = null;
    let sources = [];
    let webSources = [];

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let newlineIdx;
      while ((newlineIdx = buffer.indexOf("\n")) !== -1) {
        const line = buffer.slice(0, newlineIdx);
        buffer = buffer.slice(newlineIdx + 1);
        if (!line.trim()) continue;

        const chunk = JSON.parse(line);
        if (chunk.token) {
          if (!bubble) {
            pending.remove();
            bubble = beginStreamingMessage();
          }
          fullText += chunk.token;
          bubble.innerHTML = renderMarkdown(fullText);
          messagesScrollEl.scrollTop = messagesScrollEl.scrollHeight;
        } else if (chunk.done) {
          sources = chunk.sources || [];
          webSources = chunk.web_sources || [];
        }
      }
    }

    if (!bubble) {
      pending.remove();
      bubble = beginStreamingMessage();
    }
    appendSourcesToBubble(bubble, sources, webSources);

    history.push({ role: "assistant", content: fullText, sources, webSources });
    persistCurrentChat();
  } catch (err) {
    pending.remove();
    addMessage("assistant", "Something went wrong reaching the server.");
  } finally {
    input.focus();
  }
}

input.addEventListener("input", () => {
  const hasText = input.value.trim().length > 0;
  sendBtn.disabled = !hasText;
  sendBtn.classList.toggle("ready", hasText);
  autoGrow();
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

sendBtn.addEventListener("click", sendMessage);

let mediaRecorder = null;
let recordedChunks = [];

async function toggleRecording() {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    return;
  }

  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (err) {
    addMessage("assistant", "Couldn't access your microphone — check your browser's permission settings.");
    return;
  }

  recordedChunks = [];
  mediaRecorder = new MediaRecorder(stream);
  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size > 0) recordedChunks.push(e.data);
  };
  mediaRecorder.onstop = async () => {
    stream.getTracks().forEach((track) => track.stop());
    micBtn.classList.remove("recording");

    const blob = new Blob(recordedChunks, { type: "audio/webm" });
    const formData = new FormData();
    formData.append("audio", blob, "recording.webm");

    micBtn.disabled = true;
    try {
      const res = await fetch("/api/transcribe", { method: "POST", body: formData });
      const data = await res.json();
      if (data.text) {
        input.value = input.value ? `${input.value} ${data.text}` : data.text;
        input.dispatchEvent(new Event("input"));
        autoGrow();
        input.focus();
      }
    } catch (err) {
      addMessage("assistant", "Transcription failed — something went wrong reaching the server.");
    } finally {
      micBtn.disabled = false;
    }
  };

  mediaRecorder.start();
  micBtn.classList.add("recording");
}

micBtn.addEventListener("click", toggleRecording);

newChatBtn.addEventListener("click", () => {
  switchView("nebula");
  history = [];
  setActiveChatId(null);
  showEmptyState();
  renderChatList();
});

function switchView(view) {
  if (view === currentView) {
    brandEl.classList.remove("open");
    return;
  }
  currentView = view;
  brandEl.classList.remove("open");

  for (const item of brandDropdown.querySelectorAll(".brand-dropdown-item")) {
    item.classList.toggle("active", item.dataset.view === view);
  }

  if (view === "health") {
    brandLabel.textContent = "NOVA Health";
    workspaceLabel.textContent = "NOVA Health";
    workspaceSub.textContent = "Photo-based calorie & nutrient tracking";
    topbarTip.textContent = "Tip: Upload a photo of your meal to get started";
    nebulaView.hidden = true;
    healthView.hidden = false;
    chatListEl.hidden = true;
    healthSidebar.hidden = false;
    if (!healthMessageList) showHealthEmptyState();
    loadHealthLog();
  } else {
    brandLabel.textContent = "NOVA Nebula";
    workspaceLabel.textContent = "General workspace";
    workspaceSub.textContent = "RAG over your notes · web search when needed";
    topbarTip.textContent = "Tip: Try typing /nova and then /supernova in the chat!";
    nebulaView.hidden = false;
    healthView.hidden = true;
    chatListEl.hidden = false;
    healthSidebar.hidden = true;
  }
}

brandEl.addEventListener("click", (e) => {
  e.stopPropagation();
  brandEl.classList.toggle("open");
});

for (const item of brandDropdown.querySelectorAll(".brand-dropdown-item")) {
  item.addEventListener("click", (e) => {
    e.stopPropagation();
    switchView(item.dataset.view);
  });
}

document.addEventListener("click", () => brandEl.classList.remove("open"));

setGreeting();
renderSuggestions();

const initialChat = chats.find(c => c.id === activeChatId);
if (initialChat) {
  history = initialChat.messages.slice();
  clearMessageArea();
  for (const m of history) {
    addMessage(m.role, m.content, m.sources, m.webSources);
  }
} else {
  setActiveChatId(null);
}
renderChatList();
