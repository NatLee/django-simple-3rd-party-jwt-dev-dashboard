// Dev dashboard JavaScript, shared by every page. base.html includes this file inline.
//
// Paths and storage keys come from data-* attributes on <body>, which base.html fills from the
// URLconf, DEV_DASHBOARD_SETTINGS and django-simple-third-party-jwt's settings.
//
// show_login_error(), show_verified_token(), get_jwt_using_google_credential() and logout()
// keep the names and arguments they had in earlier versions, so templates that override
// dashboard.html or login.html and call them keep working. Plain JavaScript: no library is loaded.

function dd_config(name) {
  return document.body.getAttribute("data-" + name) || "";
}

// The tokens live in localStorage under the keys django-simple-third-party-jwt's Microsoft login
// writes them to (its MICROSOFT_JWT_REDIRECT_*_TOKEN_KEY settings), so every login shows up here.
var dd_tokens = {
  access: function () { return localStorage.getItem(dd_config("access-token-key")); },
  refresh: function () { return localStorage.getItem(dd_config("refresh-token-key")); },
  // A refresh answer brings a new refresh token only with Simple JWT's ROTATE_REFRESH_TOKENS.
  save: function (access, refresh) {
    localStorage.setItem(dd_config("access-token-key"), access);
    if (refresh) localStorage.setItem(dd_config("refresh-token-key"), refresh);
  },
  clear: function () {
    localStorage.removeItem(dd_config("access-token-key"));
    localStorage.removeItem(dd_config("refresh-token-key"));
  }
};

// POST form fields; resolve with the JSON answer, or reject with { status, responseText }
// (the fields show_login_error() has always read from its argument).
function dd_post(url, fields, accessToken) {
  var headers = {
    "Accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
  };
  if (accessToken) headers.Authorization = "Bearer " + accessToken;
  return fetch(url, { method: "POST", headers: headers, body: new URLSearchParams(fields), credentials: "same-origin" })
    .then(function (response) {
      return response.text().then(function (text) {
        var data = null;
        try { data = text ? JSON.parse(text) : {}; } catch (e) { /* not JSON */ }
        if (!response.ok || data === null) throw { status: response.status, responseText: text };
        return data;
      });
    }, function (error) {
      throw { status: 0, responseText: String((error && error.message) || error) };
    });
}

// A short, readable reason from an error answer: Simple JWT's "detail", a field error, or the text.
function dd_error_text(xhr) {
  var text = (xhr && xhr.responseText) || "";
  if (xhr && xhr.status === 0) return "The server could not be reached (" + (text || "network error") + ").";
  try {
    var data = JSON.parse(text);
    if (data && data.detail) return String(data.detail);
    if (data && typeof data === "object") {
      return Object.keys(data).map(function (key) {
        var value = data[key];
        return key + ": " + (Array.isArray(value) ? value.join(" ") : value);
      }).join("; ");
    }
  } catch (e) { /* not JSON */ }
  text = text.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
  return text ? text.slice(0, 200) : "HTTP " + (xhr && xhr.status);
}

// The banner under the top bar, for messages that do not belong to a card.
function dd_notice(message, tone) {
  var box = document.getElementById("dd-notice");
  if (!box) { console.warn(message); return; }
  box.className = "dd-alert dd-alert--" + (tone || "info");
  document.getElementById("dd-notice-text").textContent = message;
  box.hidden = !message;
}

// A message carried over to the next page (sessionStorage, this tab only).
function dd_set_flash(message) {
  try { sessionStorage.setItem("dev_dashboard_flash", message); } catch (e) { /* storage off */ }
}
function dd_take_flash() {
  try {
    var message = sessionStorage.getItem("dev_dashboard_flash") || "";
    sessionStorage.removeItem("dev_dashboard_flash");
    return message;
  } catch (e) { return ""; }
}

var DD_JWT_STATES = { none: "Not logged in", checking: "Checking…", verified: "Verified", error: "Rejected" };

function dd_set_jwt_state(state) {
  var card = document.querySelector("[data-jwt-state]");
  if (card) card.setAttribute("data-jwt-state", state);
  var status = document.getElementById("jwt-status");
  if (status) status.textContent = DD_JWT_STATES[state];
  var copy = document.getElementById("copy-token");
  if (copy) copy.disabled = state !== "verified";
}

function dd_set_result(message, tone) {
  var result = document.getElementById("result");
  if (!result) return false;
  result.textContent = message;
  result.setAttribute("data-tone", tone);
  return true;
}

function dd_set_token_placeholder(message) {
  var box = document.getElementById("token");
  if (!box) return;
  box.textContent = message;
  box.setAttribute("data-empty", "");
  dd_show_claims(null);
}

// "Bearer " + the token, with its header, payload and signature in their own colours.
// The element's text stays exactly "Bearer <token>".
function dd_show_token(token) {
  var box = document.getElementById("token");
  if (!box) return;
  box.textContent = "";
  box.removeAttribute("data-empty");
  var scheme = document.createElement("span");
  scheme.className = "dd-jwt-scheme";
  scheme.textContent = "Bearer ";
  box.appendChild(scheme);
  var names = ["header", "payload", "signature"];
  String(token).split(".").forEach(function (part, i) {
    if (i) {
      var dot = document.createElement("span");
      dot.className = "dd-jwt-dot";
      dot.textContent = ".";
      box.appendChild(dot);
    }
    var span = document.createElement("span");
    span.className = "dd-jwt-part dd-jwt-part--" + (names[i] || "signature");
    span.textContent = part;
    box.appendChild(span);
  });
  dd_show_claims(dd_decode(token));
}

// The token's payload as an object, or null. Reading it needs no key; only the server can verify it.
function dd_decode(token) {
  try {
    var part = String(token).split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    while (part.length % 4) part += "=";
    var bytes = atob(part);
    var escaped = "";
    for (var i = 0; i < bytes.length; i++) escaped += "%" + ("0" + bytes.charCodeAt(i).toString(16)).slice(-2);
    var claims = JSON.parse(decodeURIComponent(escaped));
    return claims && typeof claims === "object" ? claims : null;
  } catch (e) { return null; }
}

function dd_relative(seconds) {
  var ahead = seconds >= 0;
  var s = Math.abs(Math.round(seconds));
  var text = s < 60 ? s + " s"
    : s < 3600 ? Math.floor(s / 60) + " min " + (s % 60) + " s"
    : s < 172800 ? Math.floor(s / 3600) + " h " + Math.floor((s % 3600) / 60) + " min"
    : Math.floor(s / 86400) + " days";
  return ahead ? "in " + text : text + " ago";
}

var dd_clock = null;

function dd_show_claims(claims) {
  var list = document.getElementById("claims");
  if (!list) return;
  if (dd_clock) { clearInterval(dd_clock); dd_clock = null; }
  list.textContent = "";
  list.hidden = !claims;
  if (!claims) return;
  var expiry = null;
  Object.keys(claims).forEach(function (key) {
    var dt = document.createElement("dt");
    dt.textContent = key;
    var dd = document.createElement("dd");
    var value = claims[key];
    var isTime = (key === "exp" || key === "iat" || key === "nbf") && typeof value === "number";
    dd.textContent = isTime ? new Date(value * 1000).toISOString().replace(".000Z", "Z") : (typeof value === "object" ? JSON.stringify(value) : String(value));
    if (isTime) {
      var when = document.createElement("span");
      when.className = "dd-when";
      when.setAttribute("data-at", value);
      if (key === "exp") expiry = when;
      dd.appendChild(when);
    }
    list.appendChild(dt);
    list.appendChild(dd);
  });
  var tick = function () {
    Array.prototype.forEach.call(list.querySelectorAll(".dd-when"), function (when) {
      var left = Number(when.getAttribute("data-at")) - Date.now() / 1000;
      when.textContent = dd_relative(left);
      if (when === expiry && left < 0) when.setAttribute("data-expired", "");
    });
  };
  tick();
  dd_clock = setInterval(tick, 1000);
}

// Show "please log in again" and the server's reason. `xhr` is anything with a responseText.
function show_login_error(xhr) {
  var message = "Please log in again. The server said: " + dd_error_text(xhr);
  dd_set_jwt_state("error");
  if (document.getElementById("token")) dd_set_token_placeholder("The stored token was not accepted.");
  if (!dd_set_result(message, "error")) dd_notice(message, "error");
}

// Ask the verify URL about an access token; if it is valid, show it in the JWT card.
// `message` goes in front of "Token verified successfully!".
function show_verified_token(access_token, message) {
  dd_set_jwt_state("checking");
  return dd_post(dd_config("jwt-verify-url"), { token: access_token }, access_token).then(function () {
    dd_show_token(access_token);
    dd_set_jwt_state("verified");
    dd_set_result((message ? message + " " : "") + "Token verified successfully!", "ok");
  }, show_login_error);
}

// On every dashboard visit: if the browser keeps a JWT, refresh it, then verify and show the new one.
function refresh_stored_token() {
  var access = dd_tokens.access();
  var refresh = dd_tokens.refresh();
  var flash = dd_take_flash();
  if (!access) {
    dd_set_jwt_state("none");
    dd_set_result("", "");
    if (flash) dd_notice(flash, "info");
    return Promise.resolve();
  }
  dd_set_jwt_state("checking");
  return dd_post(dd_config("jwt-refresh-url"), { refresh: refresh || "" }).then(function (data) {
    dd_tokens.save(data.access, data.refresh);
    return show_verified_token(data.access, flash);
  }, show_login_error);
}

// Called by Sign in with Google (data-callback in base.html): trade the Google credential for a
// JWT from django-simple-third-party-jwt, keep it, and verify it.
function get_jwt_using_google_credential(response) {
  dd_notice("Checking your Google account…", "info");
  return dd_post(dd_config("google-token-url"), { credential: response.credential }).then(function (data) {
    dd_tokens.save(data.access, data.refresh);
    dd_notice("", "info");
    if (document.getElementById("token")) return show_verified_token(data.access, "3rd party login!");
    dd_set_flash("3rd party login!");
    window.location.href = dd_config("dashboard-url");
  }, function (xhr) {
    dd_notice("Google login did not work. The server said: " + dd_error_text(xhr), "error");
  });
}

// "JWT Logout": forget the tokens kept in the browser.
function logout() {
  dd_tokens.clear();
  window.location.href = dd_config("dashboard-url");
}

// Copy text to the clipboard and say so on the button for a moment.
function copy_text(text, button) {
  var done = function () {
    if (!button) return;
    var label = button.getAttribute("data-label") || button.textContent;
    button.setAttribute("data-label", label);
    button.textContent = "Copied";
    setTimeout(function () { button.textContent = label; }, 1400);
  };
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(text).then(done, function () { dd_notice("Copy failed: the browser did not allow it.", "error"); });
  }
  var area = document.createElement("textarea");
  area.value = text;
  area.setAttribute("readonly", "");
  area.style.position = "fixed";
  area.style.opacity = "0";
  document.body.appendChild(area);
  area.select();
  try { document.execCommand("copy"); done(); } catch (e) { dd_notice("Copy failed: select the text and copy it by hand.", "error"); }
  document.body.removeChild(area);
}

// The login form has two submit buttons. "JWT Login" posts to Simple JWT's token URL and keeps
// the tokens in the browser; "Session Login" is a normal form post to the dashboard's login view.
// The pressed button is the submit event's submitter; the Enter key submits with the first one.
function bind_login_form(form) {
  if (!form) return;
  form.addEventListener("submit", function (event) {
    var button = event.submitter;
    if (!button || button.value !== "jwt") return;
    event.preventDefault();
    var error = document.getElementById("login-error");
    if (error) error.hidden = true;
    var fields = {};
    Array.prototype.forEach.call(form.elements, function (element) {
      if (element.name && element.type !== "submit" && element.type !== "button") fields[element.name] = element.value;
    });
    button.setAttribute("aria-busy", "true");
    button.disabled = true;
    dd_post(dd_config("jwt-token-url"), fields).then(function (data) {
      dd_tokens.save(data.access, data.refresh);
      window.location.href = dd_config("dashboard-url");
    }, function (xhr) {
      button.removeAttribute("aria-busy");
      button.disabled = false;
      var message = "JWT login did not work: " + dd_error_text(xhr);
      if (error) {
        error.querySelector(".dd-alert__text").textContent = message;
        error.hidden = false;
      } else {
        dd_notice(message, "error");
      }
    });
  });
}
