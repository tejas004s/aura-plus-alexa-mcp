/**
 * app.js - Aura+ Alexa+ Multi-Modal Client & MCP Apps Controller
 */

// DOM Elements
const alexaOrb = document.getElementById("alexa-orb");
const orbStatus = document.getElementById("orb-status");
const dialogueFeed = document.getElementById("dialogue-feed");
const mcpAppsCanvas = document.getElementById("mcp-apps-canvas");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const voiceBtn = document.getElementById("voice-btn");
const traceTimeline = document.getElementById("trace-timeline");
const execTimeBadge = document.getElementById("exec-time-badge");
const tabTrace = document.getElementById("tab-trace");
const tabMemory = document.getElementById("tab-memory");
const tabContentTrace = document.getElementById("tab-content-trace");
const tabContentMemory = document.getElementById("tab-content-memory");
const memoryToggleBtn = document.getElementById("memory-toggle-btn");

let isRecording = false;
let recognition = null;

// Initialize Speech Recognition if supported
if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRec();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-US";

  recognition.onstart = () => {
    isRecording = true;
    voiceBtn.classList.add("recording");
    setOrbState("listening", "Listening to your voice...");
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    userInput.value = transcript;
    setOrbState("thinking", "Transcribing & orchestrating...");
    submitPrompt(transcript);
  };

  recognition.onerror = (event) => {
    console.warn("Speech recognition error:", event.error);
    stopRecording();
  };

  recognition.onend = () => {
    stopRecording();
  };
}

function toggleRecording() {
  if (!recognition) {
    alert("Speech recognition is not natively supported in this browser. Please use text input or standard Chrome.");
    return;
  }
  if (isRecording) {
    recognition.stop();
  } else {
    recognition.start();
  }
}

function stopRecording() {
  isRecording = false;
  voiceBtn.classList.remove("recording");
  if (!alexaOrb.classList.contains("thinking")) {
    setOrbState("idle", "Alexa+ is ready. Ask or tap a showcase workflow above.");
  }
}

if (voiceBtn) {
  voiceBtn.addEventListener("click", toggleRecording);
}

// Orb State Manager
function setOrbState(state, text) {
  alexaOrb.className = `alexa-orb ${state}`;
  if (orbStatus && text) {
    orbStatus.textContent = text;
  }
}

// Speak aloud using SpeechSynthesis
function speakAloud(text) {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.05;
  utterance.pitch = 1.0;

  utterance.onstart = () => {
    setOrbState("speaking", "Alexa+ is speaking...");
  };
  utterance.onend = () => {
    setOrbState("idle", "Alexa+ is ready. Ask or tap a showcase workflow above.");
  };
  utterance.onerror = () => {
    setOrbState("idle", "Alexa+ is ready. Ask or tap a showcase workflow above.");
  };

  window.speechSynthesis.speak(utterance);
}

// Tab Switching
function switchSidebarTab(tabName) {
  if (tabName === "trace") {
    tabTrace.classList.add("active");
    tabMemory.classList.remove("active");
    tabContentTrace.classList.add("active");
    tabContentMemory.classList.remove("active");
  } else {
    tabMemory.classList.add("active");
    tabTrace.classList.remove("active");
    tabContentMemory.classList.add("active");
    tabContentTrace.classList.remove("active");
  }
}

if (memoryToggleBtn) {
  memoryToggleBtn.addEventListener("click", () => {
    switchSidebarTab("memory");
  });
}

// 1-Click Judge Showcase Prompts
function runShowcase(scenario) {
  let promptText = "";
  if (scenario === "grand_slam") {
    promptText = "My parents are visiting this Friday evening for dinner and staying the weekend. Prepare the house, plan a vegetarian Italian dinner with wine pairings, check dietary restrictions from past notes, order missing groceries via Amazon Cart, set the thermostat and ambient lighting schedule, and block my calendar for Saturday morning family brunch.";
  } else if (scenario === "allergy_audit") {
    promptText = "Audit our household memory for all member dietary restrictions and food allergies before I go grocery shopping.";
  } else if (scenario === "wine_ambiance") {
    promptText = "Set the dining room to Tuscan Sunset ambiance with 71 degrees thermostat, amber lighting, and play Dad's favorite Chianti and acoustic jazz.";
  }
  userInput.value = promptText;
  submitPrompt(promptText);
}

// Submit Prompt to Orchestrator API
async function submitPrompt(prompt) {
  if (!prompt || !prompt.trim()) return;

  // Append user message bubble
  appendDialogueMessage("user", prompt);
  userInput.value = "";
  setOrbState("thinking", "AgentCore Orchestrating: Bedrock + MCP Tools...");

  try {
    const response = await fetch("/api/converse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: prompt })
    });

    const data = await response.json();

    if (data.status === "success") {
      // 1. Spoken voice response
      appendDialogueMessage("assistant", data.spoken_response);
      speakAloud(data.spoken_response);

      // 2. Render execution trace
      renderExecutionTrace(data.execution_trace, data.metadata);

      // 3. Render Generative UI (MCP Apps)
      renderMCPApps(data.mcp_apps);

      // Ensure trace tab is active
      switchSidebarTab("trace");
    } else {
      appendDialogueMessage("assistant", "An error occurred while orchestrating your request: " + (data.error || "Unknown"));
      setOrbState("idle", "Error occurred.");
    }
  } catch (err) {
    console.error("Converse API error:", err);
    appendDialogueMessage("assistant", "Connection error with Alexa+ Orchestrator. Is the server running?");
    setOrbState("idle", "Connection error.");
  }
}

// Event Listeners for Input
if (sendBtn) {
  sendBtn.addEventListener("click", () => {
    submitPrompt(userInput.value);
  });
}

if (userInput) {
  userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      submitPrompt(userInput.value);
    }
  });
}

// Append Message to Dialogue Feed
function appendDialogueMessage(sender, text) {
  const bubble = document.createElement("div");
  bubble.className = `message-bubble ${sender}-message`;
  const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  bubble.innerHTML = `
    <div class="message-header">
      <span class="message-sender">${sender === "user" ? "You" : "Aura+ Concierge"}</span>
      <span class="message-time">${timeStr}</span>
    </div>
    <div class="message-body">${text}</div>
  `;
  dialogueFeed.appendChild(bubble);
  dialogueFeed.scrollTop = dialogueFeed.scrollHeight;
}

// Render Execution Trace Timeline
function renderExecutionTrace(traceEvents, metadata) {
  if (execTimeBadge && metadata) {
    execTimeBadge.querySelector(".meta-val").textContent = `${metadata.execution_time_ms} ms`;
  }

  traceTimeline.innerHTML = "";
  if (!traceEvents || traceEvents.length === 0) return;

  traceEvents.forEach(evt => {
    const item = document.createElement("div");
    item.className = `trace-item stage-${evt.stage}`;
    
    let detailsHtml = "";
    if (evt.details) {
      detailsHtml = `<div class="trace-details">${JSON.stringify(evt.details, null, 2)}</div>`;
    }

    item.innerHTML = `
      <div class="trace-top">
        <span class="trace-agent">${evt.agent}</span>
        <span class="trace-time">${evt.timestamp}</span>
      </div>
      <div class="trace-action"><strong>[${evt.stage}]</strong> ${evt.action}</div>
      ${detailsHtml}
    `;
    traceTimeline.appendChild(item);
  });
  traceTimeline.scrollTop = traceTimeline.scrollHeight;
}

// Render MCP Apps (Generative UI Cards & Carousels)
function renderMCPApps(mcpApps) {
  mcpAppsCanvas.innerHTML = "";
  if (!mcpApps || mcpApps.length === 0) return;

  mcpApps.forEach(app => {
    if (app.component === "MCPAppCarousel" || app.type === "recipe_menu_carousel") {
      mcpAppsCanvas.appendChild(createRecipeCarouselApp(app));
    } else if (app.type === "amazon_fresh_checkout") {
      mcpAppsCanvas.appendChild(createAmazonCartApp(app));
    } else if (app.type === "smart_ambiance_scene") {
      mcpAppsCanvas.appendChild(createAmbianceApp(app));
    } else if (app.type === "calendar_event_confirmation") {
      mcpAppsCanvas.appendChild(createCalendarApp(app));
    }
  });

  mcpAppsCanvas.scrollTop = 0;
}

// Component 1: Recipe Carousel
function createRecipeCarouselApp(app) {
  const card = document.createElement("div");
  card.className = "mcp-card";

  let cardsHtml = "";
  (app.cards || []).forEach(c => {
    let badges = (c.dietary_badges || []).map(b => `<span class="diet-badge ${b.includes('Allergy') ? 'critical' : ''}">${b}</span>`).join("");
    cardsHtml += `
      <div class="carousel-card">
        <img src="${c.image_url}" alt="${c.title}" class="carousel-img">
        <div class="carousel-body">
          <span class="course-label">${c.course}</span>
          <h4 class="recipe-title">${c.title}</h4>
          <div class="badge-row">${badges}</div>
          <div class="chef-note">👨‍🍳 ${c.chef_notes}</div>
        </div>
      </div>
    `;
  });

  card.innerHTML = `
    <div class="mcp-card-header">
      <div class="mcp-card-title-group">
        <h3>🍽️ ${app.title}</h3>
        <p>${app.subtitle}</p>
      </div>
      <span class="mcp-badge">MCP App: Carousel</span>
    </div>
    <div class="carousel-wrapper">
      <div class="carousel-container">${cardsHtml}</div>
    </div>
  `;
  return card;
}

// Component 2: Amazon Fresh Checkout Card with 1-Click Purchase Approval
function createAmazonCartApp(app) {
  const card = document.createElement("div");
  card.className = "mcp-card";
  const cart = app.data || {};

  let itemsHtml = "";
  (cart.items || []).forEach(item => {
    itemsHtml += `
      <div class="cart-item-row">
        <div class="cart-item-left">
          <img src="${item.image_url}" alt="${item.name}" class="cart-thumb">
          <div>
            <div class="cart-item-name">${item.name}</div>
            <div class="cart-item-brand">${item.brand} (Qty: ${item.quantity})</div>
          </div>
        </div>
        <div class="cart-item-price">$${item.line_total.toFixed(2)}</div>
      </div>
    `;
  });

  card.innerHTML = `
    <div class="mcp-card-header">
      <div class="mcp-card-title-group">
        <h3>🛒 ${app.title}</h3>
        <p>${app.subtitle}</p>
      </div>
      <span class="mcp-badge">MCP App: Fresh Cart</span>
    </div>
    <div class="cart-items-list">${itemsHtml}</div>
    <div class="cart-financial-summary">
      <div class="financial-row">
        <span>Subtotal</span>
        <span>$${cart.subtotal ? cart.subtotal.toFixed(2) : '58.44'}</span>
      </div>
      <div class="financial-row">
        <span>Prime Fresh Delivery</span>
        <span style="color: var(--accent-green)">FREE</span>
      </div>
      <div class="financial-row">
        <span>Estimated Tax</span>
        <span>$${cart.estimated_tax ? cart.estimated_tax.toFixed(2) : '3.80'}</span>
      </div>
      <div class="financial-row total-row">
        <span>Total (${cart.delivery_window || 'Friday Doorstep'})</span>
        <span style="color: var(--accent-cyan)">$${cart.total ? cart.total.toFixed(2) : '62.24'}</span>
      </div>
    </div>
    <div class="cart-actions">
      <button id="approve-purchase-btn" class="btn-approve-purchase" onclick="executePurchaseApproval('${cart.cart_id}')">
        <span>✓ Approve & Place Order ($${cart.total ? cart.total.toFixed(2) : '62.24'})</span>
      </button>
    </div>
  `;
  return card;
}

// 1-Click Purchase Approval Handler
async function executePurchaseApproval(cartId) {
  const btn = document.getElementById("approve-purchase-btn");
  if (!btn) return;
  btn.innerHTML = "<span>Processing Amazon Checkout...</span>";

  try {
    const res = await fetch("/api/cart/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cart_id: cartId })
    });
    const result = await res.json();
    if (result.success) {
      btn.className = "btn-approve-purchase confirmed";
      btn.innerHTML = `<span>✓ Order Confirmed (${result.order_id})</span>`;
      appendDialogueMessage("assistant", `Order confirmed! ${result.message} Order ID: ${result.order_id}`);
      speakAloud(`Your Amazon Fresh order is confirmed for Friday delivery.`);
    }
  } catch (err) {
    console.error("Purchase execution error:", err);
    btn.innerHTML = "<span>Retry Approval</span>";
  }
}

// Component 3: Smart Ambiance Scene Widget
function createAmbianceApp(app) {
  const card = document.createElement("div");
  card.className = "mcp-card";
  const state = app.data || {};

  card.innerHTML = `
    <div class="mcp-card-header">
      <div class="mcp-card-title-group">
        <h3>💡 ${app.title}</h3>
        <p>${app.subtitle}</p>
      </div>
      <span class="mcp-badge">MCP App: IoT Scene</span>
    </div>
    <div class="ambiance-controls">
      <div class="slider-group">
        <div class="slider-label-row">
          <span>Target Climate</span>
          <span id="temp-display" class="slider-val">${state.climate ? state.climate.target_temp_f : 71}°F</span>
        </div>
        <input 
          type="range" 
          id="temp-slider" 
          class="styled-slider" 
          min="65" 
          max="78" 
          value="${state.climate ? state.climate.target_temp_f : 71}"
          oninput="handleAmbianceChange()"
        >
      </div>
      <div class="slider-group">
        <div class="slider-label-row">
          <span>Lighting Brightness</span>
          <span id="bright-display" class="slider-val">${state.lighting ? state.lighting.brightness_pct : 45}%</span>
        </div>
        <input 
          type="range" 
          id="bright-slider" 
          class="styled-slider" 
          min="10" 
          max="100" 
          value="${state.lighting ? state.lighting.brightness_pct : 45}"
          oninput="handleAmbianceChange()"
        >
      </div>
    </div>
    <div class="music-stream-widget">
      <div class="music-info">
        <span style="font-size: 1.2rem">🎶</span>
        <div>
          <div class="music-track">${state.audio ? state.audio.now_playing : 'Warm Acoustic Dinner Jazz'}</div>
          <div class="music-service">Amazon Music HD • Living Area</div>
        </div>
      </div>
      <span style="font-size: 0.8rem; color: var(--accent-green); font-weight: 700;">● STREAM READY</span>
    </div>
  `;
  return card;
}

// Live Ambiance Sliders Handler
async function handleAmbianceChange() {
  const tempSlider = document.getElementById("temp-slider");
  const brightSlider = document.getElementById("bright-slider");
  const tempDisplay = document.getElementById("temp-display");
  const brightDisplay = document.getElementById("bright-display");

  if (tempSlider && tempDisplay) {
    tempDisplay.textContent = `${tempSlider.value}°F`;
  }
  if (brightSlider && brightDisplay) {
    brightDisplay.textContent = `${brightSlider.value}%`;
  }

  // Debounce API update
  clearTimeout(window._ambianceTimer);
  window._ambianceTimer = setTimeout(async () => {
    try {
      await fetch("/api/ambiance/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scene_name: "Tuscan Sunset",
          target_temp_f: tempSlider.value,
          brightness_pct: brightSlider.value
        })
      });
    } catch (e) {
      console.warn("Ambiance update error:", e);
    }
  }, 400);
}

// Component 4: Calendar Event Card
function createCalendarApp(app) {
  const card = document.createElement("div");
  card.className = "mcp-card";
  const evt = app.data || {};

  card.innerHTML = `
    <div class="mcp-card-header">
      <div class="mcp-card-title-group">
        <h3>📅 ${app.title}</h3>
        <p>${app.subtitle}</p>
      </div>
      <span class="mcp-badge">MCP App: Calendar</span>
    </div>
    <div class="calendar-card-body">
      <div>
        <div class="cal-title">${evt.title}</div>
        <div class="cal-time">🕒 ${evt.start} - ${evt.end}</div>
        <div class="cal-attendees">👥 Attendees: ${(evt.attendees || []).join(', ')}</div>
      </div>
      <button class="header-btn" onclick="alert('Calendar invites sent to ' + '${(evt.attendees || []).join(', ')}')">
        Send Invites
      </button>
    </div>
  `;
  return card;
}

// Teach New Memory Fact Handler
async function commitNewMemory() {
  const memberInput = document.getElementById("teach-member");
  const factInput = document.getElementById("teach-fact");
  if (!memberInput || !factInput || !factInput.value.trim()) return;

  const member = memberInput.value.trim() || "Mom";
  const fact = factInput.value.trim();

  try {
    const res = await fetch("/api/memory/remember", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        member_name: member,
        preference: fact,
        category: fact.toLowerCase().includes("allerg") ? "allergy" : "preference"
      })
    });
    const result = await res.json();
    if (result.success) {
      alert(`Memory updated! Alexa+ now remembers: "${fact}" for ${member}.`);
      factInput.value = "";
      location.reload();
    }
  } catch (err) {
    console.error("Error saving memory:", err);
  }
}
