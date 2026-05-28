let chatBox = document.getElementById("chat-box");
let typing = document.getElementById("typing");

let lastType = "";

chatBox.scrollTop = chatBox.scrollHeight;

// START SESSION
window.onload = function () {

    if (!sessionStorage.getItem("sessionStarted")) {
        fetch("/start-session").then(() => {
            sessionStorage.setItem("sessionStarted", "true");
        });
    }

    loadSessions();
};

window.addEventListener("DOMContentLoaded", () => {
    loadUser();
});

// ENTER KEY
function handleKey(e) {

    // Shift + Enter → next line
    if (e.key === "Enter" && e.shiftKey) {
        return;
    }

    // Enter only → send
    if (e.key === "Enter") {
        e.preventDefault();
        sendMessage();
    }
}


function addMessage(text, type){

    let div = document.createElement("div");
    div.classList.add("bubble", type);

    let msgText = document.createElement("div");
    msgText.classList.add("msg-text");
    msgText.innerText = text;

    div.appendChild(msgText);

    // only user msgs
    if(type === "user"){

        let actions = document.createElement("div");
        actions.classList.add("msg-actions");

        // COPY
        let copyBtn = document.createElement("button");
        copyBtn.innerText = "⿻";

        copyBtn.onclick = () => {
            navigator.clipboard.writeText(text);
        };

        // EDIT
        let editBtn = document.createElement("button");
        editBtn.innerText = "🖊";

        editBtn.onclick = () => {

            let input = document.getElementById("msg");

            // remove emoji prefix if present
            let clean = text.replace(/^🧑\s*/, "");

            input.value = clean;

            input.focus();

            // optional remove bubble
            div.remove();
        };

        actions.appendChild(copyBtn);
        actions.appendChild(editBtn);

        div.appendChild(actions);
    }

    chatBox.appendChild(div);

    lastType = type;
    chatBox.scrollTop = chatBox.scrollHeight;
}
// SAVE CHAT
// function saveChat(text, type) {
//     let chats = JSON.parse(localStorage.getItem("chatHistory")) || [];
//     chats.push({text, type});
//     localStorage.setItem("chatHistory", JSON.stringify(chats));
// }

// ✅ RECENT CHAT (FIXED POSITION)
// let sessionStarted = sessionStorage.getItem("topicAdded") === "true";

// function updateRecentChat(msg){

//     if(sessionStarted) return;   // 🔥 only first message

//     let topic = msg.split(" ").slice(0,4).join(" ");

//     let div = document.createElement("div");
//     div.innerText = topic || "New Chat";
//     div.classList.add("session-item");

//     div.onclick = () => loadSession(topic);  // 🔥 click support

//     document.getElementById("sessions").prepend(div);

//     sessionStarted = true;
// }

function loadSessions(){

    fetch("/sessions")
    .then(res => res.json())
    .then(data => {

        let container = document.getElementById("sessions");
        container.innerHTML = "";

        data.forEach(s => {

            let div = document.createElement("div");

            div.classList.add("session-item");

            // 🔥 fallback if no topic
            div.innerText = s.topic ? s.topic : "Thinking...";

            // 👉 click → load chat later
            div.onclick = () => {
                loadSession(s.session_id);   // 🔥 pass ID not topic
            };

            container.appendChild(div);
        });

    });
}

// MENU
function openMenu(){
    let modal = document.getElementById("menuModal");
    if(modal){
        modal.classList.remove("hidden");
        modal.style.display = "flex";   // 🔥 FORCE OPEN
    }
}

function closeMenu(){
    let modal = document.getElementById("menuModal");
    if(modal){
        modal.classList.add("hidden");
        modal.style.display = "none";   // 🔥 FORCE CLOSE
    }
}

// 🔥 WAIT FOR DOM
window.addEventListener("DOMContentLoaded", () => {

    let modal = document.getElementById("menuModal");
    let content = document.querySelector(".modal-content");

    if(modal && content){   // 🔥 NULL CHECK FIX

        modal.addEventListener("click", (e) => {
            if(e.target === modal){
                closeMenu();
            }
        });

        content.addEventListener("click", (e) => {
            e.stopPropagation();
        });

    }
});

// OTHER ACTIONS
function openAnalytics(){
    window.location.href = "/user/analytics";
}

async function openProfile(){

    let res = await fetch("/get-user");
    let data = await res.json();

    let name = data.name || "User";
    let username = data.username || "user";

    let joinedText = "Joined: Not available";

    if (data.created_at) {
        let date = new Date(data.created_at);

        let formatted = date.toLocaleString("en-IN", {
            day: "numeric",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });

        joinedText = "Joined: " + formatted;
    }

    alert(
`👤 Name: ${name}
🆔 Username: ${username}
📅 ${joinedText}`
    );
}

function logout(){
    let confirmLogout = confirm("Are you sure you want to logout?");
    if(!confirmLogout) return;

    // 🔥 SHOW CUSTOM RATING MODAL
    let modal = document.getElementById("ratingModal");
    if(modal){
        modal.classList.remove("hidden");
        modal.style.display = "flex";
    }
    sessionStorage.removeItem("sessionStarted");
    sessionStorage.removeItem("topicAdded");
}


async function loadUser(){

    let res = await fetch("/get-user");
    let data = await res.json();

    let name = data.name || "User";
    let email = data.email || "";

    // 🔥 name
    document.querySelector(".name").innerText = name;
    //email
    document.querySelector(".email").innerText = email;
    // 🔥 initials (RS logic)
    let parts = name.trim().split(/\s+/);

    let initial = parts.length >= 2
        ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
        : parts[0][0].toUpperCase();

    document.querySelector(".avatar").innerText = initial;

    // 🔥 joining date (NEW)
    if (data.created_at) {
        let date = new Date(data.created_at);
        document.querySelector(".joined").innerText =
            "Joined: " + date.toLocaleDateString();
    }
}

// 🚀 MAIN CHAT FUNCTION
async function sendMessage() {

    let input = document.getElementById("msg");
    let msg = input.value.trim();

    if (!msg) return;

    addMessage("🧑 " + msg, "user");

    input.value = "";

    typing.classList.remove("hidden");

    await new Promise(r => setTimeout(r, 800));

    try {
        let res = await fetch("/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({message: msg})
        });

        let data = await res.json();

        typing.classList.add("hidden");

        addMessage("🤖 " + data.reply, "bot");

        // 🔥 THIS IS KEY
        if (data.topic) {
    // 🔥 direct UI update
            let firstSession = document.querySelector(".session-item");

            if (firstSession) {
                firstSession.innerText = data.topic;
            }
        } else {
            // 🔄 fallback: reload sessions
            loadSessions();
        }
    } catch (err) {
        typing.classList.add("hidden");
        addMessage("⚠️ Server error", "bot");
    }

}

// ================= UI ENHANCEMENTS (SAFE ADDITIONS ONLY) =================

// ✨ Remove welcome screen when first message comes
function removeWelcome() {
    let welcome = document.querySelector(".welcome");
    if (welcome) welcome.remove();
}

// ✨ Hook into existing addMessage WITHOUT modifying it
const originalAddMessage = addMessage;

addMessage = function(text, type) {
    removeWelcome();  // remove welcome when chat starts
    originalAddMessage(text, type);
};


// ✨ Quick option buttons support
function quickMsg(text) {
    let input = document.getElementById("msg");
    input.value = text;
    sendMessage();
}


// ✨ Typing dots auto-create (if spans missing)
window.addEventListener("DOMContentLoaded", () => {
    let typingDiv = document.getElementById("typing");

    if (typingDiv && typingDiv.children.length === 0) {
        typingDiv.innerHTML = "<span></span><span></span><span></span>";
    }
});


// ✨ Auto focus input (small UX improvement)
window.addEventListener("DOMContentLoaded", () => {
    let input = document.getElementById("msg");
    if (input) input.focus();
});


// ✨ Scroll improvement (smooth bottom stick)
const originalSendMessage = sendMessage;

sendMessage = async function() {
    await originalSendMessage();

    // ensure scroll always goes bottom
    chatBox.scrollTop = chatBox.scrollHeight;
};


// ✨ Click outside menu closes it (extra polish)
document.addEventListener("click", function(e) {
    let modal = document.getElementById("menuModal");
    let content = document.querySelector(".modal-content");

    if (!modal || modal.classList.contains("hidden")) return;

    // 🔥 ignore clicks inside modal
    if (content.contains(e.target)) return;

    // 🔥 ignore menu button click
    if (e.target.closest(".menu-btn")) return;

    closeMenu();
});


window.addEventListener("DOMContentLoaded", () => {
    let modal = document.getElementById("menuModal");
    if(modal){
        modal.classList.add("hidden");
        modal.style.display = "none";
    }
});

function showWelcome(){
    let div = document.createElement("div");
    div.classList.add("welcome");

    div.innerHTML = `
        <h3>👋 Hi, I’m here for you</h3>
        <p>How are you feeling today?</p>
        <div class="quick-options">
            <button onclick="quickMsg('I feel sad')">😔 Sad</button>
            <button onclick="quickMsg('I feel anxious')">😟 Anxious</button>
            <button onclick="quickMsg('I feel okay')">😊 Okay</button>
            <button onclick="quickMsg('Just want to talk')">💬 Talk</button>
        </div>
    `;

    chatBox.appendChild(div);
}

async function startNewChat(){

    await fetch("/start-session");

    chatBox.innerHTML = "";
    lastType = "";

    showWelcome();   // 🔥 ADD THIS

    sessionStorage.setItem("sessionStarted", "true");

    loadSessions();
}

let selectedRating = 0;

function rate(value) {
    selectedRating = value;

    let stars = document.querySelectorAll(".stars span");

    stars.forEach((star, index) => {
        if(index < value){
            star.classList.add("active");
        } else {
            star.classList.remove("active");
        }
    });
}

function submitRating(){

    if(selectedRating === 0){
        alert("Please select rating");
        return;
    }

    fetch("/submit-rating", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ rating: selectedRating })
    });

    fetch("/logout");   // 🔥 ADD THIS

    window.location.href = "/login";
}

function skipRating(){

    fetch("/logout");   // 🔥 ADD THIS

    window.location.href = "/login";
}

window.addEventListener("DOMContentLoaded", () => {
    let modal = document.getElementById("ratingModal");
    if(modal){
        modal.classList.add("active");
        modal.style.display = "none";
    }
});

async function filterChats(){

    let input = document.getElementById("searchInput").value.trim();

    let container = document.getElementById("sessions");

    if(input === ""){
        loadSessions();   // 🔥 reset
        return;
    }

    let res = await fetch(`/search-sessions?q=${input}`);
    let data = await res.json();

    container.innerHTML = "";

    data.forEach(s => {
        if(data.length === 0){
            container.innerHTML = `
                <p style="color:white; padding:20px;">
                    No chats found for this username
                </p>
            `;
            return;
        }

        let div = document.createElement("div");
        div.classList.add("session-item");

        div.innerText = s.topic ? s.topic : "Matched Chat";

        div.onclick = () => {
            loadSession(s.session_id);
        };

        container.appendChild(div);
    });
}

async function loadAdminData() {
    let searchValue = document.getElementById("searchInput").value.trim();

    let res = await fetch(`/admin/data?search=${searchValue}`);
    let data = await res.json();

    let container = document.getElementById("chatLogs");
    container.innerHTML = "";

    data.forEach(chat => {
        container.innerHTML += `
            <div class="chat-card">
                <h4>${chat.username}</h4>
                <p><strong>User:</strong> ${chat.message_text}</p>
                <p><strong>Bot:</strong> ${chat.bot_response}</p>
                <p>Emotion: ${chat.emotion_label}</p>
                <p>Crisis: ${chat.is_crisis_flag}</p>
            </div>
        `;
    });
}
function loadSession(sessionId){

    // 🔥 reset search
    let input = document.getElementById("searchInput");
    if(input) input.value = "";

    let chats = document.querySelectorAll(".session-item");
    chats.forEach(c => c.style.display = "block");

    // existing code
    fetch(`/switch-session/${sessionId}`);
    fetch(`/get-session/${sessionId}`)
    .then(res => res.json())
    .then(data => {
        chatBox.innerHTML = "";
        lastType = "";

        data.forEach(chat => {
            addMessage("🧑 " + chat.message_text, "user");
            addMessage("🤖 " + chat.bot_response, "bot");
        });
    });
}

let redirectPath = "";

// 🔥 open modal instead of direct redirect
function openDisclaimer(path){
    redirectPath = path;

    let modal = document.getElementById("disclaimerModal");
    if(modal){
        modal.classList.add("active");   // 🔥 FIX
    }
}

// 🔥 checkbox enable button
window.addEventListener("DOMContentLoaded", () => {

    let check = document.getElementById("agreeCheck");
    let btn = document.getElementById("continueBtn");

    if(check && btn){

        check.addEventListener("change", function(){

            if(this.checked){
                btn.disabled = false;
                btn.classList.add("enabled");
            } else {
                btn.disabled = true;
                btn.classList.remove("enabled");
            }
        });

        btn.addEventListener("click", function(){
            window.location.href = redirectPath;
        });

    }
});

function handleSignup(){

    let data = {
        name: document.getElementById("name").value,
        username: document.getElementById("username").value,
        email: document.getElementById("email").value,
        password: document.getElementById("password").value
    };

    signupUser(data);
}

function signupUser(data){

    fetch("/signup", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(response => {
        if (response.success) {
            window.location.href = "/chat-page";   // 🔥 redirect
        } else {
            alert(response.message);
        }
    })
    .catch(() => {
        alert("Server error");
    });
}

async function sendOTP() {

    const btn = document.getElementById("sendOtpBtn");

    if (btn.disabled) return;

    btn.disabled = true;
    btn.innerText = "Sending...";

    try {
        const email = document.getElementById("email").value;

        const res = await fetch("/send-otp", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email })
        });

        const data = await res.json();

        alert(data.message);

    } catch (err) {
        console.error(err);
        alert("OTP send failed");
    } finally {
        btn.disabled = false;
        btn.innerText = "Send Email OTP";
    }
}
