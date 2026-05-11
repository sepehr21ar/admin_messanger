// common.js

const API_URL = "http://127.0.0.1:8000";

function getToken() {
  return localStorage.getItem("token");
}

function authHeaders() {
  return {
    "Content-Type": "application/json",
    "Authorization": "Bearer " + getToken()
  };
}

function logout() {
  localStorage.removeItem("token");
  window.location.href = "login.html";
}

function parseToken() {
  const token = getToken();
  if (!token) return null;
  return JSON.parse(atob(token.split('.')[1]));
}

async function loadInbox() {
  const res = await fetch(API_URL + "/messages/inbox", { headers: authHeaders() });
  const inbox = await res.json();
  const list = document.getElementById("inbox");
  list.innerHTML = "";

  inbox.forEach(m => {
    const li = document.createElement("li");
    li.textContent = `📨 ${m.title} — از: ${m.sender}`;
    if (!m.is_read) li.classList.add("unread");
    li.onclick = () => openMessage(m.id, li);
    list.appendChild(li);
  });
}

async function openMessage(id, li=null) {
  const res = await fetch(`${API_URL}/messages/${id}`, { headers: authHeaders() });
  const m = await res.json();

  document.getElementById("view_title").innerText = m.title;
  document.getElementById("view_sender").innerText = "✉️ فرستنده: " + (m.sender || "سیستم");
  document.getElementById("view_content").innerText = m.content;

  if (li && li.classList.contains("unread")) {
    await fetch(`${API_URL}/messages/${id}/read`, { method: "POST", headers: authHeaders() });
    li.classList.remove("unread");
  }
}

async function loadSent() {
  const res = await fetch(API_URL + "/messages/sent", { headers: authHeaders() });
  const sent = await res.json();
  const list = document.getElementById("sent");
  list.innerHTML = "";

  sent.forEach(m => {
    // نام گیرندگان
    const recipientNames = m.receivers ? m.receivers.map(u => u.username).join(", ") : m.receivers_count || "";
    const li = document.createElement("li");
    li.textContent = `📤 ${m.title} → ${recipientNames}`;
    li.onclick = () => openSentMessage(m);
    list.appendChild(li);
  });
}

function openSentMessage(m) {
  document.getElementById("view_title").innerText = m.title;
  document.getElementById("view_sender").innerText = "فرستنده: " + (parseToken()?.username || "ادمین");
  document.getElementById("view_content").innerText = m.content;
}

async function loadUsers() {
  const res = await fetch(API_URL + "/admin/users", { headers: authHeaders() });
  const users = await res.json();
  const list = document.getElementById("users");
  window.usersCache = users; 
  list.innerHTML = "";
  users.forEach(u => {
    const li = document.createElement("li");
    li.textContent = `${u.id} - ${u.username} (${u.role})`;
    list.appendChild(li);
  });
}

async function createUser(username, password, role, msgElementId="msg") {
  const res = await fetch(API_URL + "/admin/create-user", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ username, password, role })
  });
  const data = await res.json();
  if (msgElementId) document.getElementById(msgElementId).innerText = data.message;
  loadUsers();
}

async function sendMessage(title, content, user_ids, msgElementId="msg") {
  const res = await fetch(API_URL + "/messages/send", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ title, content, user_ids })
  });
  const data = await res.json();
  if (msgElementId) document.getElementById(msgElementId).innerText = data.message;
}
