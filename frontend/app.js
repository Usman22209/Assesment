/**
 * Frontend Application Logic for Dar Global & Wasalt AI Assistant.
 * Handles RAG chat, streaming responses, citation badges, and settings.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const messagesContainer = document.getElementById("messagesContainer");
  const welcomeHero = document.getElementById("welcomeHero");
  const queryInput = document.getElementById("queryInput");
  const sendBtn = document.getElementById("sendBtn");
  const scopeSelector = document.getElementById("scopeSelector");
  const activeModelBadge = document.getElementById("activeModelBadge");
  const modelNameDisplay = document.getElementById("modelNameDisplay");

  // Settings Modal Elements
  const settingsModal = document.getElementById("settingsModal");
  const openSettingsBtn = document.getElementById("openSettingsBtn");
  const closeSettingsBtn = document.getElementById("closeSettingsBtn");
  const cancelSettingsBtn = document.getElementById("cancelSettingsBtn");
  const saveSettingsBtn = document.getElementById("saveSettingsBtn");
  const openrouterApiKeyInput = document.getElementById("openrouterApiKey");
  const modelSelect = document.getElementById("modelSelect");
  const streamToggle = document.getElementById("streamToggle");

  // State
  let currentScope = "all";
  let conversationHistory = [];
  let isGenerating = false;

  // Local Storage Settings
  let userApiKey = localStorage.getItem("openrouter_api_key") || "";
  let selectedModel = localStorage.getItem("selected_model") || "meta-llama/llama-3.3-70b-instruct:free";
  let enableStreaming = localStorage.getItem("enable_streaming") !== "false";

  // Initial Sync
  openrouterApiKeyInput.value = userApiKey;
  modelSelect.value = selectedModel;
  streamToggle.checked = enableStreaming;
  modelNameDisplay.textContent = selectedModel;

  // Fetch API Health & Stats
  fetchStats();

  async function fetchStats() {
    try {
      const res = await fetch("/api/stats");
      if (res.ok) {
        const data = await res.json();
        const pills = document.getElementById("statsPills");
        if (pills && data.total_documents) {
          pills.innerHTML = `
            <div class="stat-item">
              <span class="stat-number">${data.total_documents}</span>
              <span class="stat-label">Verified Docs</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">$23B</span>
              <span class="stat-label">Dar Global GDV</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">${data.wasalt_documents}</span>
              <span class="stat-label">Wasalt Sources</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">Free</span>
              <span class="stat-label">OpenRouter Tier</span>
            </div>
          `;
        }
      }
    } catch (e) {
      console.warn("Could not load stats:", e);
    }
  }

  // Auto-resize textarea
  queryInput.addEventListener("input", () => {
    queryInput.style.height = "auto";
    queryInput.style.height = Math.min(queryInput.scrollHeight, 120) + "px";
  });

  // Handle enter key submit
  queryInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });

  sendBtn.addEventListener("click", handleSend);

  // Scope Selector
  scopeSelector.addEventListener("click", (e) => {
    const btn = e.target.closest(".scope-btn");
    if (!btn) return;
    scopeSelector.querySelectorAll(".scope-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    currentScope = btn.dataset.scope;
  });

  // Suggestion Cards
  document.querySelectorAll(".suggestion-card").forEach((card) => {
    card.addEventListener("click", () => {
      const prompt = card.dataset.prompt;
      if (prompt) {
        queryInput.value = prompt;
        handleSend();
      }
    });
  });

  // Settings Modal Handlers
  openSettingsBtn.addEventListener("click", () => settingsModal.classList.add("open"));
  closeSettingsBtn.addEventListener("click", () => settingsModal.classList.remove("open"));
  cancelSettingsBtn.addEventListener("click", () => settingsModal.classList.remove("open"));
  settingsModal.addEventListener("click", (e) => {
    if (e.target === settingsModal) settingsModal.classList.remove("open");
  });

  saveSettingsBtn.addEventListener("click", () => {
    userApiKey = openrouterApiKeyInput.value.trim();
    selectedModel = modelSelect.value;
    enableStreaming = streamToggle.checked;

    localStorage.setItem("openrouter_api_key", userApiKey);
    localStorage.setItem("selected_model", selectedModel);
    localStorage.setItem("enable_streaming", enableStreaming);

    modelNameDisplay.textContent = selectedModel;
    settingsModal.classList.remove("open");
  });

  // Chat Execution
  async function handleSend() {
    const text = queryInput.value.trim();
    if (!text || isGenerating) return;

    // Hide welcome hero on first message
    if (welcomeHero) {
      welcomeHero.style.display = "none";
    }

    // Append User Message
    appendMessage("user", text);
    queryInput.value = "";
    queryInput.style.height = "auto";
    conversationHistory.push({ role: "user", content: text });

    // Show Typing Indicator
    isGenerating = true;
    sendBtn.disabled = true;
    const typingId = appendTypingIndicator();

    const scopeFilter = currentScope === "all" ? null : currentScope;

    try {
      if (enableStreaming) {
        await executeStreamingChat(text, scopeFilter, typingId);
      } else {
        await executeStandardChat(text, scopeFilter, typingId);
      }
    } catch (err) {
      removeTypingIndicator(typingId);
      appendMessage(
        "assistant",
        `⚠️ **Error encountered**: ${err.message || "Failed to communicate with service."}`
      );
    } finally {
      isGenerating = false;
      sendBtn.disabled = false;
      queryInput.focus();
    }
  }

  // Standard Chat (Non-streaming)
  async function executeStandardChat(query, scopeFilter, typingId) {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: query,
        history: conversationHistory.slice(-6),
        source_filter: scopeFilter,
        model: selectedModel,
        user_api_key: userApiKey || null,
        stream: false,
      }),
    });

    removeTypingIndicator(typingId);

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Server returned ${response.status}: ${err}`);
    }

    const data = await response.json();
    appendMessage("assistant", data.reply, data.citations);
    conversationHistory.push({ role: "assistant", content: data.reply });
  }

  // Streaming Chat (SSE)
  async function executeStreamingChat(query, scopeFilter, typingId) {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: query,
        history: conversationHistory.slice(-6),
        source_filter: scopeFilter,
        model: selectedModel,
        user_api_key: userApiKey || null,
        stream: true,
      }),
    });

    removeTypingIndicator(typingId);

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Server returned ${response.status}: ${err}`);
    }

    // Create assistant bubble for streaming
    const { bubble, citationContainer } = createAssistantMessageShell();
    let accumulatedText = "";
    let citations = [];

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop(); // keep remainder

      for (const block of lines) {
        if (!block.trim()) continue;
        const eventMatch = block.match(/^event: (.*)$/m);
        const dataMatch = block.match(/^data: (.*)$/m);

        const event = eventMatch ? eventMatch[1].trim() : "message";
        const rawData = dataMatch ? dataMatch[1].trim() : "";

        if (event === "citations") {
          try {
            citations = JSON.parse(rawData);
            renderCitations(citationContainer, citations);
          } catch (e) {
            console.error("Error parsing citations:", e);
          }
        } else if (event === "message") {
          try {
            const tokenObj = JSON.parse(rawData);
            accumulatedText += tokenObj.token;
            bubble.innerHTML = marked.parse(accumulatedText);
            scrollToBottom();
          } catch (e) {
            // Raw text fallback
            accumulatedText += rawData;
            bubble.innerHTML = marked.parse(accumulatedText);
            scrollToBottom();
          }
        } else if (event === "end") {
          break;
        }
      }
    }

    conversationHistory.push({ role: "assistant", content: accumulatedText });
  }

  // UI Render Helpers
  function appendMessage(role, text, citations = []) {
    const row = document.createElement("div");
    row.className = `message-row ${role}`;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = role === "user" ? "👤" : "🏛️";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";

    if (role === "assistant" && window.marked) {
      bubble.innerHTML = marked.parse(text);
    } else {
      bubble.textContent = text;
    }

    // Attach citations if available
    if (role === "assistant" && citations && citations.length > 0) {
      const citationContainer = document.createElement("div");
      citationContainer.className = "citations-card";
      renderCitations(citationContainer, citations);
      bubble.appendChild(citationContainer);
    }

    if (role === "user") {
      row.appendChild(bubble);
      row.appendChild(avatar);
    } else {
      row.appendChild(avatar);
      row.appendChild(bubble);
    }

    messagesContainer.appendChild(row);
    scrollToBottom();
  }

  function createAssistantMessageShell() {
    const row = document.createElement("div");
    row.className = "message-row assistant";

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = "🏛️";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";

    const citationContainer = document.createElement("div");
    citationContainer.className = "citations-card";

    bubble.appendChild(citationContainer);
    row.appendChild(avatar);
    row.appendChild(bubble);
    messagesContainer.appendChild(row);
    scrollToBottom();

    return { row, bubble, citationContainer };
  }

  function renderCitations(container, citations) {
    if (!citations || citations.length === 0) return;
    container.innerHTML = `
      <div class="citations-header">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
        </svg>
        <span>Verified Sources Grounding This Answer</span>
      </div>
      <div class="citations-list"></div>
    `;

    const list = container.querySelector(".citations-list");
    citations.forEach((c) => {
      const isDG = c.source.toLowerCase().includes("dar");
      const pill = document.createElement("a");
      pill.className = "citation-pill";
      pill.href = c.url || "#";
      pill.target = "_blank";
      pill.title = `${c.title}\nCategory: ${c.category}\nExcerpt: ${c.snippet || ""}`;
      pill.innerHTML = `
        <span class="pill-source-badge ${isDG ? "dg" : "wasalt"}">${isDG ? "Dar Global" : "Wasalt"}</span>
        <span>${escapeHtml(c.title.split("-")[0].trim())}</span>
      `;
      list.appendChild(pill);
    });
  }

  function appendTypingIndicator() {
    const id = "typing-" + Date.now();
    const row = document.createElement("div");
    row.className = "message-row assistant";
    row.id = id;

    row.innerHTML = `
      <div class="message-avatar">🏛️</div>
      <div class="message-bubble" style="padding: 10px 16px;">
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    `;
    messagesContainer.appendChild(row);
    scrollToBottom();
    return id;
  }

  function removeTypingIndicator(id) {
    const elem = document.getElementById(id);
    if (elem) elem.remove();
  }

  function scrollToBottom() {
    const viewport = document.querySelector(".chat-viewport");
    if (viewport) {
      viewport.scrollTop = viewport.scrollHeight;
    }
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
