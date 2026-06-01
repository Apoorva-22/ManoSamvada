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

function handleLoginKey(e){

    if(e.key === "Enter"){
        e.preventDefault();
        login();
    }
}

function togglePassword(){

    const pass = document.getElementById("password");

    if(pass.type === "password"){
        pass.type = "text";
    }else{
        pass.type = "password";
    }
}

function addMessage(text, type){

    let div = document.createElement("div");
    div.classList.add("bubble", type);

    
    let msgWrap = document.createElement("div");
    msgWrap.classList.add("msg-wrap");

    
    if(type === "user"){
        let icon = document.createElement("span");
        icon.classList.add("user-icon");
        icon.innerText = "🧑";
        msgWrap.appendChild(icon);
    }

    let msgText = document.createElement("div");
    msgText.classList.add("msg-text");
    msgText.innerText = text;

    msgWrap.appendChild(msgText);
    div.appendChild(msgWrap);

    // actions
    if(type === "user"){

        let actions = document.createElement("div");
        actions.classList.add("msg-actions");

        // copy
        let copyBtn = document.createElement("button");
        copyBtn.innerText = "📋";

        copyBtn.onclick = () => {
            navigator.clipboard.writeText(msgText.innerText);
        };

        // edit
        let editBtn = document.createElement("button");
        editBtn.innerText = "✏️";

        editBtn.onclick = () => {

            msgText.contentEditable = true;
            msgText.focus();

            msgText.onkeydown = async function(e){

                if(e.key === "Enter" && !e.shiftKey){

                    e.preventDefault();

                    msgText.contentEditable = false;

                    let edited = msgText.innerText.trim();

                    // remove everything below this bubble
                    let next = div.nextSibling;

                    while(next){
                        let temp = next.nextSibling;
                        next.remove();
                        next = temp;
                    }

                
                    await resendEditedMessage(edited);
                }
            };

            msgText.onblur = function(){
                msgText.contentEditable = false;
            };
        };

        actions.appendChild(copyBtn);
        actions.appendChild(editBtn);

        div.appendChild(actions);
    }

    chatBox.appendChild(div);

    lastType = type;
    chatBox.scrollTop = chatBox.scrollHeight;
}



function loadSessions(){

    fetch("/sessions")
    .then(res => res.json())
    .then(data => {

        let container = document.getElementById("sessions");
        container.innerHTML = "";

        data.forEach(s => {

            let div = document.createElement("div");

            div.classList.add("session-item");

           
            div.innerText = s.topic ? s.topic : "Thinking...";

            
            div.onclick = () => {
                loadSession(s.session_id);   
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
        modal.style.display = "flex";   
    }
}

function closeMenu(){
    let modal = document.getElementById("menuModal");
    if(modal){
        modal.classList.add("hidden");
        modal.style.display = "none";   
    }
}

// WAIT FOR DOM
window.addEventListener("DOMContentLoaded", () => {

    let modal = document.getElementById("menuModal");
    let content = document.querySelector(".modal-content");

    if(modal && content){   

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

    
    document.querySelector(".name").innerText = name;
    /
    document.querySelector(".email").innerText = email;
    
    let parts = name.trim().split(/\s+/);

    let initial = parts.length >= 2
        ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
        : parts[0][0].toUpperCase();

    document.querySelector(".avatar").innerText = initial;

   
    if (data.created_at) {
        let date = new Date(data.created_at);
        document.querySelector(".joined").innerText =
            "Joined: " + date.toLocaleDateString();
    }
}

// MAIN CHAT FUNCTION
async function sendMessage() {

    let input = document.getElementById("msg");
    let msg = input.value.trim();

    if (!msg) return;

    addMessage(msg, "user");

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

        
        if (data.topic) {
  
            let firstSession = document.querySelector(".session-item");

            if (firstSession) {
                firstSession.innerText = data.topic;
            }
        } else {
            
            loadSessions();
        }
    } catch (err) {
        typing.classList.add("hidden");
        addMessage("⚠️ Server error", "bot");
    }

}

async function resendEditedMessage(text){

    const r = await fetch("/chat", {
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body: JSON.stringify({
            message:text
        })
    });

    const data = await r.json();

    addMessage(data.reply, "bot");

    loadSessions();
}


function removeWelcome() {
    let welcome = document.querySelector(".welcome");
    if (welcome) welcome.remove();
}


const originalAddMessage = addMessage;

addMessage = function(text, type) {
    removeWelcome();  
    originalAddMessage(text, type);
};



function quickMsg(text) {
    let input = document.getElementById("msg");
    input.value = text;
    sendMessage();
}



window.addEventListener("DOMContentLoaded", () => {
    let typingDiv = document.getElementById("typing");

    if (typingDiv && typingDiv.children.length === 0) {
        typingDiv.innerHTML = "<span></span><span></span><span></span>";
    }
});



window.addEventListener("DOMContentLoaded", () => {
    let input = document.getElementById("msg");
    if (input) input.focus();
});


const originalSendMessage = sendMessage;

sendMessage = async function() {
    await originalSendMessage();

    
    chatBox.scrollTop = chatBox.scrollHeight;
};



document.addEventListener("click", function(e) {
    let modal = document.getElementById("menuModal");
    let content = document.querySelector(".modal-content");

    if (!modal || modal.classList.contains("hidden")) return;

    
    if (content.contains(e.target)) return;

    
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

    showWelcome();   

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

    fetch("/logout");   

    window.location.href = "/login";
}

function skipRating(){

    fetch("/logout");   

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
        loadSessions();   
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

   
    let input = document.getElementById("searchInput");
    if(input) input.value = "";

    let chats = document.querySelectorAll(".session-item");
    chats.forEach(c => c.style.display = "block");


    fetch(`/switch-session/${sessionId}`);
    fetch(`/get-session/${sessionId}`)
    .then(res => res.json())
    .then(data => {
        chatBox.innerHTML = "";
        lastType = "";

        data.forEach(chat => {
            addMessage(chat.message_text, "user");
            addMessage(chat.bot_response, "bot");
        });
    });
}

let redirectPath = "";


function openDisclaimer(path){
    redirectPath = path;

    let modal = document.getElementById("disclaimerModal");
    if(modal){
        modal.classList.add("active");   
    }
}


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
            window.location.href = "/chat-page";  
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
