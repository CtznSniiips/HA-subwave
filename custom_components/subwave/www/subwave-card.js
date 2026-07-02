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
      show_requests: true,
      show_dj: true,
    };
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Please select a SUB/WAVE media player entity.");
    }
    this._config = { show_requests: true, show_dj: true, ...config };
    this._requesterName = window.localStorage.getItem("subwave-card-name") || "";
    this._playing = false;
    this._sending = false;
    this._buildDom();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return this._config && this._config.show_requests ? 6 : 4;
  }

  connectedCallback() {
    this._render();
  }

  disconnectedCallback() {
    this._stopAudio();
  }

  _buildDom() {
    this.innerHTML = `
      <ha-card>
        <div class="subwave-card">
          <div class="art-row">
            <img class="art" alt="" />
            <div class="meta">
              <div class="title">—</div>
              <div class="artist"></div>
              <div class="dj"></div>
            </div>
            <button class="play-btn" type="button" title="Play">
              <ha-icon icon="mdi:play"></ha-icon>
            </button>
          </div>
          <div class="status-row">
            <span class="listeners"></span>
            <input type="range" class="volume" min="0" max="1" step="0.05" value="1" title="Volume" />
          </div>
          <form class="request-form">
            <input type="text" class="req-text" placeholder="Request a song or a vibe…" maxlength="200" />
            <input type="text" class="req-name" placeholder="Your name (optional)" maxlength="60" />
            <button type="submit" class="req-submit">Send</button>
          </form>
          <div class="feedback"></div>
        </div>
      </ha-card>
      <style>
        .subwave-card { padding: 12px 16px 16px; }
        .art-row { display: flex; align-items: center; gap: 12px; }
        .art {
          width: 56px; height: 56px; border-radius: 8px; object-fit: cover;
          background: var(--divider-color); flex-shrink: 0;
        }
        .meta { flex: 1; min-width: 0; }
        .title {
          font-weight: 500; font-size: 1rem; color: var(--primary-text-color);
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .artist {
          font-size: 0.875rem; color: var(--secondary-text-color);
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .dj { font-size: 0.75rem; color: var(--secondary-text-color); opacity: 0.8; margin-top: 2px; }
        .play-btn {
          background: var(--primary-color); border: none; border-radius: 50%;
          width: 44px; height: 44px; display: flex; align-items: center;
          justify-content: center; cursor: pointer; color: white; flex-shrink: 0;
          padding: 0;
        }
        .play-btn ha-icon { --mdc-icon-size: 24px; }
        .status-row {
          display: flex; align-items: center; justify-content: space-between;
          margin-top: 10px; gap: 12px; min-height: 20px;
        }
        .listeners { font-size: 0.75rem; color: var(--secondary-text-color); }
        .volume { flex: 1; max-width: 120px; }
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
        .feedback { font-size: 0.8rem; margin-top: 6px; min-height: 1em; }
        .feedback.error { color: var(--error-color, #db4437); }
        .feedback.ok { color: var(--success-color, #43a047); }
      </style>
    `;

    this._els = {
      card: this.querySelector("ha-card"),
      art: this.querySelector(".art"),
      title: this.querySelector(".title"),
      artist: this.querySelector(".artist"),
      dj: this.querySelector(".dj"),
      playBtn: this.querySelector(".play-btn"),
      playIcon: this.querySelector(".play-btn ha-icon"),
      listeners: this.querySelector(".listeners"),
      volume: this.querySelector(".volume"),
      form: this.querySelector(".request-form"),
      reqText: this.querySelector(".req-text"),
      reqName: this.querySelector(".req-name"),
      reqSubmit: this.querySelector(".req-submit"),
      feedback: this.querySelector(".feedback"),
    };

    this._els.playBtn.addEventListener("click", () => this._togglePlayback());

    this._els.volume.addEventListener("input", (event) => {
      if (this._audio) this._audio.volume = parseFloat(event.target.value);
    });

    this._els.reqName.value = this._requesterName;
    this._els.reqName.addEventListener("change", (event) => {
      this._requesterName = event.target.value.trim();
      window.localStorage.setItem("subwave-card-name", this._requesterName);
    });

    this._els.form.addEventListener("submit", (event) => {
      event.preventDefault();
      this._sendRequest();
    });

    if (!this._config.show_requests) {
      this._els.form.style.display = "none";
    }
  }

  _render() {
    if (!this._hass || !this._config || !this._els) return;

    const stateObj = this._hass.states[this._config.entity];
    this._els.card.header = this._config.title || undefined;

    if (!stateObj) {
      this._els.title.textContent = "Entity not found";
      this._els.artist.textContent = this._config.entity;
      return;
    }

    const attrs = stateObj.attributes;

    if (attrs.entity_picture) {
      this._els.art.src = attrs.entity_picture;
      this._els.art.style.visibility = "visible";
    } else {
      this._els.art.style.visibility = "hidden";
    }

    this._els.title.textContent = attrs.media_title || "Nothing playing";
    this._els.artist.textContent = [attrs.media_artist, attrs.media_album_name]
      .filter(Boolean)
      .join(" — ");

    if (this._config.show_dj && (attrs.dj_name || attrs.dj_tagline)) {
      this._els.dj.textContent = [attrs.dj_name, attrs.dj_tagline].filter(Boolean).join(" · ");
      this._els.dj.style.display = "";
    } else {
      this._els.dj.style.display = "none";
    }

    const listeners = attrs.listeners_current;
    this._els.listeners.textContent =
      listeners === undefined || listeners === null
        ? ""
        : `${listeners} listening${listeners === 1 ? "" : "s"}`;

    this._els.playIcon.setAttribute("icon", this._playing ? "mdi:stop" : "mdi:play");
    this._els.playBtn.title = this._playing ? "Stop" : "Play";

    this._streamUrl = attrs.proxy_stream_url || attrs.stream_url || null;
    this._requestsEndpoint = attrs.requests_endpoint || null;

    this._els.playBtn.disabled = !this._streamUrl;
    this._els.reqSubmit.disabled = this._sending || !this._requestsEndpoint;
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
      this._audio.volume = parseFloat(this._els.volume.value || "1");
      this._audio.addEventListener("error", () => {
        this._showFeedback("Playback error - stream may be offline.", true);
        this._playing = false;
        this._render();
      });
    }
    // Set a fresh src (with a cache-busting param) each time we start, so
    // we join at the live edge instead of resuming a stale paused buffer.
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
    if (!this._els) return;
    this._els.feedback.textContent = message;
    this._els.feedback.classList.toggle("error", !!isError);
    this._els.feedback.classList.toggle("ok", !!isOk);
    if (this._feedbackTimer) clearTimeout(this._feedbackTimer);
    this._feedbackTimer = setTimeout(() => {
      if (this._els) this._els.feedback.textContent = "";
    }, 4000);
  }
}

class SubwaveCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { show_requests: true, show_dj: true, ...config };
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
        </style>
        <div class="subwave-editor">
          <div class="entity-slot"></div>
          <ha-textfield class="title-field" label="Card title (optional)"></ha-textfield>
          <div class="row">
            <label>Show request form</label>
            <ha-switch class="show-requests"></ha-switch>
          </div>
          <div class="row">
            <label>Show DJ name/tagline</label>
            <ha-switch class="show-dj"></ha-switch>
          </div>
        </div>
      `;

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

      this._showRequests = this.querySelector(".show-requests");
      this._showRequests.addEventListener("change", (event) => {
        this._updateConfig({ show_requests: event.target.checked });
      });

      this._showDj = this.querySelector(".show-dj");
      this._showDj.addEventListener("change", (event) => {
        this._updateConfig({ show_dj: event.target.checked });
      });

      this._built = true;
    }

    this._picker.hass = this._hass;
    this._picker.value = this._config.entity || "";
    this._titleField.value = this._config.title || "";
    this._showRequests.checked = this._config.show_requests !== false;
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
