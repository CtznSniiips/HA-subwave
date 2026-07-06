/* SUB/WAVE Lovelace card - custom:subwave-card
 *
 * Bundled with the SUB/WAVE Home Assistant integration and auto-registered
 * as a frontend module - no manual Lovelace resource setup needed.
 *
 * Vanilla custom elements only, no build step or external dependencies.
 * Uses HA's globally-available ha-card / ha-entity-picker / ha-textfield /
 * ha-switch / ha-icon elements, which are always present in the frontend.
 */

const CARD_TAG = "subwave-card";
const EDITOR_TAG = "subwave-card-editor";

const LAYOUTS = ["compact", "hero", "retro"];
const LAYOUT_LABELS = {
  compact: "Compact",
  hero: "Hero art",
  retro: "Retro FM",
};
const LAYOUT_BASE_SIZE = { compact: 3, hero: 7, retro: 4 };

const REQUEST_MODES = ["hidden", "always"];

// Shared across every layout: the power button (outline circle, grey glyph
// when off, red when on/playing - matching the native SUB/WAVE player) and
// the request form.
const COMMON_STYLE = `
  <style>
    .subwave-card { padding: 16px; }
    .subwave-card.requests-toggle { cursor: pointer; }
    .pwr-btn {
      background: transparent;
      border: 1px solid var(--primary-text-color);
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      cursor: pointer; padding: 0; flex-shrink: 0;
    }
    .pwr-btn:disabled { opacity: 0.4; cursor: default; }
    .pwr-icon { color: var(--secondary-text-color); }
    .pwr-btn[aria-pressed="true"] .pwr-icon { color: var(--error-color, #db4437); }
    .request-form { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
    .request-form input[type="text"] {
      flex: 1; min-width: 100px; padding: 8px 10px; border-radius: 8px;
      border: 1px solid var(--divider-color); background: var(--card-background-color);
      color: var(--primary-text-color); font: inherit;
    }
    .req-submit {
      padding: 8px 14px; border-radius: 8px; border: none;
      background: var(--primary-color); color: white; cursor: pointer; font: inherit;
    }
    .req-submit:disabled { opacity: 0.5; cursor: default; }
    .feedback { font-size: 0.8rem; margin-top: 6px; display: none; }
    .feedback.visible { display: block; }
    .feedback.error { color: var(--error-color, #db4437); }
    .feedback.ok { color: var(--success-color, #43a047); }
    .volume {
      -webkit-appearance: none;
      appearance: none;
      height: 2px;
      background: var(--divider-color);
      border-radius: 2px;
      outline: none;
      cursor: pointer;
    }
    .volume::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 12px; height: 12px;
      border-radius: 50%;
      background: var(--primary-color);
      cursor: pointer;
    }
    .volume::-moz-range-track {
      height: 2px;
      background: transparent;
      border-radius: 2px;
    }
    .volume::-moz-range-thumb {
      width: 12px; height: 12px;
      border-radius: 50%;
      background: var(--primary-color);
      border: none;
      cursor: pointer;
    }
  </style>
`;

function requestBlockHtml(config) {
  const formHtml = `
    <form class="request-form">
      <input type="text" class="req-text" placeholder="Request a song or a vibe…" maxlength="200" />
      <input type="text" class="req-name" placeholder="Your name (optional)" maxlength="60" />
      <button type="submit" class="req-submit">Send</button>
    </form>
    <div class="feedback"></div>
  `;
  if (config.requests_mode === "hidden") {
    return `<div class="request-wrap" style="display:none;">${formHtml}</div>`;
  }
  return `<div class="request-wrap">${formHtml}</div>`;
}

const POWER_BTN_HTML = `
  <button class="pwr-btn" type="button" aria-label="Power" aria-pressed="false">
    <ha-icon class="pwr-icon" icon="mdi:power"></ha-icon>
  </button>
`;

function layoutTemplate(layout, config) {
  const requestBlock = requestBlockHtml(config);
  const toggleClass = config.requests_mode === "hidden" ? " requests-toggle" : "";

  if (layout === "hero") {
    return `
      <ha-card>
        <div class="subwave-card layout-hero${toggleClass}">
          <div class="art-wrap"><img class="art" alt="" /></div>
          <div class="title">—</div>
          <div class="artist"></div>
          <div class="subline"></div>
          <input type="range" class="volume" min="0" max="1" step="0.05" value="1" title="Volume" />
          ${POWER_BTN_HTML}
          ${requestBlock}
        </div>
        ${COMMON_STYLE}
        <style>
          .layout-hero { text-align: center; }
          .layout-hero .art-wrap {
            width: 100%; max-width: 220px; margin: 0 auto 12px; aspect-ratio: 1 / 1;
            border-radius: 12px; overflow: hidden; background: var(--divider-color);
          }
          .layout-hero .art { width: 100%; height: 100%; object-fit: cover; }
          .layout-hero .title { font-weight: 500; font-size: 1.05rem; }
          .layout-hero .artist { font-size: 0.85rem; color: var(--secondary-text-color); margin-top: 2px; }
          .layout-hero .subline {
            font-size: 0.75rem; color: var(--secondary-text-color); opacity: 0.8; margin-top: 4px; min-height: 1em;
          }
          .layout-hero .volume { display: block; width: 60%; max-width: 200px; margin: 14px auto 0; }
          .layout-hero .pwr-btn { width: 56px; height: 56px; margin: 14px auto 0; }
          .layout-hero .pwr-icon { --mdc-icon-size: 26px; }
          .layout-hero .request-form { max-width: 320px; margin-left: auto; margin-right: auto; }
        </style>
      `;
  }

  if (layout === "retro") {
    return `
      <ha-card>
        <div class="subwave-card layout-retro${toggleClass}">
          <div class="top-row">
            <span class="badge"></span>
            <span class="freq"></span>
          </div>
          <div class="readout">
            <div class="readout-text">
              <div class="title">—</div>
              <div class="artist"></div>
              <div class="dj-line"></div>
            </div>
            <img class="art" alt="" />
          </div>
          <div class="controls">
            ${POWER_BTN_HTML}
            <input type="range" class="volume" min="0" max="1" step="0.05" value="1" title="Volume" />
          </div>
          ${requestBlock}
        </div>
        ${COMMON_STYLE}
        <style>
          .layout-retro .top-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
          .layout-retro .badge {
            font-size: 0.7rem; font-weight: 500; letter-spacing: 0.5px;
            background: var(--warning-color, #ff9800); color: #000;
            padding: 3px 8px; border-radius: 6px; opacity: 0.85;
          }
          .layout-retro .freq { font-family: var(--code-font-family, monospace); font-size: 0.7rem; color: var(--secondary-text-color); }
          .layout-retro .readout {
            background: var(--secondary-background-color, var(--card-background-color));
            border-radius: 8px; padding: 10px 12px; margin-bottom: 12px;
            display: flex; align-items: center; gap: 12px;
          }
          .layout-retro .readout-text { flex: 1; min-width: 0; }
          .layout-retro .art {
            width: 56px; height: 56px; border-radius: 6px; object-fit: cover;
            background: var(--divider-color); flex-shrink: 0;
          }
          .layout-retro .title {
            font-family: var(--code-font-family, monospace); font-size: 0.85rem; letter-spacing: 0.5px;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-transform: uppercase;
          }
          .layout-retro .artist {
            font-family: var(--code-font-family, monospace); font-size: 0.75rem; color: var(--secondary-text-color);
            margin-top: 2px; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
          }
          .layout-retro .dj-line {
            font-family: var(--code-font-family, monospace); font-size: 0.7rem; color: var(--secondary-text-color);
            margin-top: 4px; text-transform: uppercase; opacity: 0.7; min-height: 1em;
          }
          .layout-retro .controls { display: flex; align-items: center; gap: 12px; }
          .layout-retro .pwr-btn { width: 44px; height: 44px; }
          .layout-retro .volume { flex: 1; }
        </style>
      `;
  }

  // compact (default)
  return `
      <ha-card>
        <div class="subwave-card layout-compact${toggleClass}">
          <div class="art-row">
            <img class="art" alt="" />
            <div class="meta">
              <div class="title">—</div>
              <div class="artist"></div>
            </div>
            <span class="station-tag"></span>
            ${POWER_BTN_HTML}
          </div>
          <div class="status-row">
            <span class="subline"></span>
            <input type="range" class="volume" min="0" max="1" step="0.05" value="1" title="Volume" />
          </div>
          ${requestBlock}
        </div>
        ${COMMON_STYLE}
        <style>
          .layout-compact .art-row { display: flex; align-items: center; gap: 12px; }
          .layout-compact .art { width: 40px; height: 40px; border-radius: 8px; object-fit: cover; background: var(--divider-color); flex-shrink: 0; }
          .layout-compact .meta { flex: 1; min-width: 0; }
          .layout-compact .title { font-weight: 500; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
          .layout-compact .artist { font-size: 0.8rem; color: var(--secondary-text-color); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
          .layout-compact .station-tag { font-size: 0.7rem; color: var(--secondary-text-color); white-space: nowrap; max-width: 90px; overflow: hidden; text-overflow: ellipsis; }
          .layout-compact .pwr-btn { width: 32px; height: 32px; }
          .layout-compact .pwr-icon { --mdc-icon-size: 16px; }
          .layout-compact .status-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 8px; min-height: 20px; }
          .layout-compact .subline { font-size: 0.75rem; color: var(--secondary-text-color); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
          .layout-compact .volume { max-width: 100px; }
        </style>
      `;
}

class SubwaveCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement(EDITOR_TAG);
  }

  static getStubConfig(hass) {
    const entity = Object.keys(hass.states).find(
      (id) =>
        id.startsWith("media_player.") &&
        "proxy_stream_url" in hass.states[id].attributes
    );
    return {
      type: `custom:${CARD_TAG}`,
      entity: entity || "",
      layout: "compact",
      requests_mode: "always",
      show_dj: true,
    };
  }

  static _resolveRequestsMode(config) {
    if (REQUEST_MODES.includes(config.requests_mode)) return config.requests_mode;
    // Back-compat for configs saved before the always/hidden modes existed.
    return config.show_requests === false ? "hidden" : "always";
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Please select a SUB/WAVE media player entity.");
    }
    const layout = LAYOUTS.includes(config.layout) ? config.layout : "compact";
    const requestsMode = SubwaveCard._resolveRequestsMode(config);
    const rebuildNeeded =
      !this._config ||
      this._config.layout !== layout ||
      this._config.requests_mode !== requestsMode;

    this._config = { show_dj: true, ...config, layout, requests_mode: requestsMode };
    this._requesterName = window.localStorage.getItem("subwave-card-name") || "";
    this._playing = this._playing || false;
    this._sending = false;

    if (rebuildNeeded || !this._built) {
      this._buildDom();
      this._built = true;
    }
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    if (!this._config) return 4;
    const base = LAYOUT_BASE_SIZE[this._config.layout] || 4;
    // "hidden" mode starts collapsed (just a one-line hint), so it doesn't
    // need the same reserved space as a form that's always visible.
    return base + (this._config.requests_mode === "always" ? 1 : 0);
  }

  connectedCallback() {
    this._render();
  }

  disconnectedCallback() {
    this._stopAudio();
  }

  _buildDom() {
    this.innerHTML = layoutTemplate(this._config.layout, this._config);
    this._collectEls();
    if (this._els.volume && this._audio) {
      this._els.volume.value = String(this._audio.volume);
    }
    this._wireEvents();
  }

  _updateVolumeFill(el) {
    if (!el) return;
    const min = parseFloat(el.min || "0");
    const max = parseFloat(el.max || "1");
    const val = parseFloat(el.value || "0");
    const pct = max > min ? ((val - min) / (max - min)) * 100 : 0;
    el.style.background = `linear-gradient(to right, var(--primary-color) 0%, var(--primary-color) ${pct}%, var(--divider-color) ${pct}%, var(--divider-color) 100%)`;
  }

  _collectEls() {
    this._els = {
      card: this.querySelector("ha-card"),
      cardBody: this.querySelector(".subwave-card"),
      art: this.querySelector(".art"),
      title: this.querySelector(".title"),
      artist: this.querySelector(".artist"),
      subline: this.querySelector(".subline"),
      djLine: this.querySelector(".dj-line"),
      stationTag: this.querySelector(".station-tag"),
      badge: this.querySelector(".badge"),
      freq: this.querySelector(".freq"),
      pwrBtn: this.querySelector(".pwr-btn"),
      pwrIcon: this.querySelector(".pwr-icon"),
      volume: this.querySelector(".volume"),
      requestWrap: this.querySelector(".request-wrap"),
      form: this.querySelector(".request-form"),
      reqText: this.querySelector(".req-text"),
      reqName: this.querySelector(".req-name"),
      reqSubmit: this.querySelector(".req-submit"),
      feedback: this.querySelector(".feedback"),
    };
  }

  _wireEvents() {
    const els = this._els;

    if (els.pwrBtn) {
      els.pwrBtn.addEventListener("click", () => this._togglePlayback());
    }

    if (els.volume) {
      this._updateVolumeFill(els.volume);
      els.volume.addEventListener("input", (event) => {
        if (this._audio) this._audio.volume = parseFloat(event.target.value);
        this._updateVolumeFill(event.target);
      });
    }

    if (els.reqName) {
      els.reqName.value = this._requesterName;
      els.reqName.addEventListener("change", (event) => {
        this._requesterName = event.target.value.trim();
        window.localStorage.setItem("subwave-card-name", this._requesterName);
      });
    }

    if (els.form) {
      els.form.addEventListener("submit", (event) => {
        event.preventDefault();
        this._sendRequest();
      });
    }

    if (this._config.requests_mode === "hidden" && els.cardBody) {
      els.cardBody.addEventListener("click", (event) => {
        if (event.target.closest("input, button, a")) return;
        this._toggleRequestForm();
      });
    }
  }

  _toggleRequestForm() {
    if (!this._els.requestWrap) return;
    const isOpen = this._els.requestWrap.style.display !== "none";
    this._els.requestWrap.style.display = isOpen ? "none" : "block";
  }

  _render() {
    if (!this._hass || !this._config || !this._els) return;

    const stateObj = this._hass.states[this._config.entity];
    if (this._els.card) this._els.card.header = this._config.title || undefined;

    if (!stateObj) {
      if (this._els.title) this._els.title.textContent = "Entity not found";
      if (this._els.artist) this._els.artist.textContent = this._config.entity;
      return;
    }

    const attrs = stateObj.attributes;

    if (this._els.art) {
      if (attrs.entity_picture) {
        this._els.art.src = attrs.entity_picture;
        this._els.art.style.visibility = "visible";
      } else {
        this._els.art.style.visibility = "hidden";
      }
    }

    if (this._els.title) this._els.title.textContent = attrs.media_title || "Nothing playing";
    if (this._els.artist) {
      this._els.artist.textContent = [attrs.media_artist, attrs.media_album_name]
        .filter(Boolean)
        .join(" — ");
    }

    const listenersCount = attrs.listeners_current;
    const listenersText =
      listenersCount === undefined || listenersCount === null
        ? null
        : `${listenersCount} listening`;

    if (this._els.stationTag) {
      this._els.stationTag.textContent = attrs.app_name || attrs.friendly_name || "";
    }

    if (this._els.subline) {
      const parts = [];
      if (this._config.show_dj && (attrs.dj_name || attrs.dj_tagline)) {
        parts.push([attrs.dj_name, attrs.dj_tagline].filter(Boolean).join(" · "));
      }
      if (listenersText) parts.push(listenersText);
      this._els.subline.textContent = parts.join(" · ");
    }

    if (this._els.djLine) {
      this._els.djLine.textContent = this._config.show_dj && attrs.dj_name ? attrs.dj_name : "";
    }

    if (this._els.badge) {
      this._els.badge.textContent = stateObj.state === "off" ? "OFFLINE" : "ON AIR";
    }
    if (this._els.freq) {
      this._els.freq.textContent = attrs.app_name || attrs.friendly_name || "";
    }

    this._streamUrl = attrs.proxy_stream_url || attrs.stream_url || null;
    this._requestsEndpoint = attrs.requests_endpoint || null;

    if (this._els.pwrBtn) {
      this._els.pwrBtn.disabled = !this._streamUrl;
      this._els.pwrBtn.setAttribute("aria-pressed", String(this._playing));
      this._els.pwrBtn.title = this._playing ? "Turn off" : "Turn on";
    }

    if (this._els.reqSubmit) {
      this._els.reqSubmit.disabled = this._sending || !this._requestsEndpoint;
    }
  }

  _togglePlayback() {
    if (this._playing) {
      this._stopAudio();
    } else {
      this._startAudio();
    }
  }

  _startAudio() {
    if (!this._streamUrl) return;
    if (!this._audio) {
      this._audio = new Audio();
      this._audio.volume = this._els.volume ? parseFloat(this._els.volume.value || "1") : 1;
      this._audio.addEventListener("error", () => {
        this._showFeedback("Playback error - stream may be offline.", true);
        this._playing = false;
        this._render();
      });
    }
    // Fresh src (with a cache-busting param) each time we power on, so we
    // join at the live edge instead of resuming a stale paused buffer.
    const sep = this._streamUrl.includes("?") ? "&" : "?";
    this._audio.src = `${this._streamUrl}${sep}_=${Date.now()}`;
    this._audio.play().catch(() => {
      this._showFeedback("Could not start playback.", true);
    });
    this._playing = true;
    this._render();
  }

  _stopAudio() {
    if (this._audio) {
      this._audio.pause();
      this._audio.removeAttribute("src");
      this._audio.load();
    }
    this._playing = false;
    this._render();
  }

  async _sendRequest() {
    if (!this._els.reqText) return;
    const text = this._els.reqText.value.trim();
    if (!text || !this._requestsEndpoint || this._sending) return;

    this._sending = true;
    this._els.reqSubmit.disabled = true;
    this._showFeedback("Sending…", false);

    const body = { text };
    if (this._requesterName) body.name = this._requesterName;

    try {
      await this._hass.callApi("POST", this._requestsEndpoint, body);
      this._showFeedback("Request sent!", false, true);
      this._els.reqText.value = "";
    } catch (err) {
      this._showFeedback("Couldn't send that request. Try again?", true);
    } finally {
      this._sending = false;
      this._els.reqSubmit.disabled = !this._requestsEndpoint;
    }
  }

  _showFeedback(message, isError, isOk) {
    if (!this._els || !this._els.feedback) return;
    this._els.feedback.textContent = message;
    this._els.feedback.classList.toggle("error", !!isError);
    this._els.feedback.classList.toggle("ok", !!isOk);
    this._els.feedback.classList.add("visible");
    if (this._feedbackTimer) clearTimeout(this._feedbackTimer);
    this._feedbackTimer = setTimeout(() => {
      if (this._els && this._els.feedback) {
        this._els.feedback.textContent = "";
        this._els.feedback.classList.remove("visible");
      }
    }, 4000);
  }
}

class SubwaveCardEditor extends HTMLElement {
  setConfig(config) {
    const layout = LAYOUTS.includes(config.layout) ? config.layout : "compact";
    const requestsMode = SubwaveCard._resolveRequestsMode(config);
    this._config = { show_dj: true, ...config, layout, requests_mode: requestsMode };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass || !this._config) return;

    if (!this._built) {
      this.innerHTML = `
        <style>
          .subwave-editor { display: flex; flex-direction: column; gap: 16px; padding: 8px 0; }
          .row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
          .row label { color: var(--primary-text-color); }
          .layout-field label {
            display: block; font-size: 12px; color: var(--secondary-text-color); margin-bottom: 4px;
          }
          .layout-field select {
            width: 100%; height: 40px; padding: 0 10px; border-radius: 8px;
            border: 1px solid var(--divider-color); background: var(--card-background-color);
            color: var(--primary-text-color); font: inherit;
          }
          .helper-text {
            font-size: 12px; color: var(--secondary-text-color);
            margin: -8px 0 0; line-height: 1.4;
          }
        </style>
        <div class="subwave-editor">
          <div class="layout-field">
            <label for="subwave-layout-select">Layout</label>
            <select id="subwave-layout-select" class="layout-select"></select>
          </div>
          <div class="entity-slot"></div>
          <ha-textfield class="title-field" label="Card title (optional)"></ha-textfield>
          <div class="row">
            <label>Request form always on</label>
            <ha-switch class="requests-toggle-switch"></ha-switch>
          </div>
          <p class="helper-text">When toggled off, tap the card to show or hide the request form.</p>
          <div class="row">
            <label>Show DJ name/tagline</label>
            <ha-switch class="show-dj"></ha-switch>
          </div>
        </div>
      `;

      this._layoutSelect = this.querySelector(".layout-select");
      LAYOUTS.forEach((key) => {
        const opt = document.createElement("option");
        opt.value = key;
        opt.textContent = LAYOUT_LABELS[key] || key;
        this._layoutSelect.appendChild(opt);
      });
      this._layoutSelect.addEventListener("change", (event) => {
        this._updateConfig({ layout: event.target.value });
      });

      this._picker = document.createElement("ha-entity-picker");
      this._picker.hass = this._hass;
      this._picker.includeDomains = ["media_player"];
      this._picker.label = "SUB/WAVE media player";
      this._picker.addEventListener("value-changed", (event) => {
        this._updateConfig({ entity: event.detail.value });
      });
      this.querySelector(".entity-slot").appendChild(this._picker);

      this._titleField = this.querySelector(".title-field");
      this._titleField.addEventListener("change", (event) => {
        this._updateConfig({ title: event.target.value || undefined });
      });

      this._requestsToggle = this.querySelector(".requests-toggle-switch");
      this._requestsToggle.addEventListener("change", (event) => {
        this._updateConfig({
          requests_mode: event.target.checked ? "always" : "hidden",
          show_requests: undefined,
        });
      });

      this._showDj = this.querySelector(".show-dj");
      this._showDj.addEventListener("change", (event) => {
        this._updateConfig({ show_dj: event.target.checked });
      });

      this._built = true;
    }

    this._layoutSelect.value = this._config.layout;
    this._picker.hass = this._hass;
    this._picker.value = this._config.entity || "";
    this._titleField.value = this._config.title || "";
    this._requestsToggle.checked = this._config.requests_mode === "always";
    this._showDj.checked = this._config.show_dj !== false;
  }

  _updateConfig(patch) {
    this._config = { ...this._config, ...patch };
    this.dispatchEvent(
      new CustomEvent("config-changed", {
        detail: { config: this._config },
        bubbles: true,
        composed: true,
      })
    );
  }
}

if (!customElements.get(CARD_TAG)) {
  customElements.define(CARD_TAG, SubwaveCard);
}
if (!customElements.get(EDITOR_TAG)) {
  customElements.define(EDITOR_TAG, SubwaveCardEditor);
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: CARD_TAG,
  name: "SUB/WAVE Radio",
  description: "Now playing, playback, and listener requests for a SUB/WAVE station.",
  preview: false,
});
