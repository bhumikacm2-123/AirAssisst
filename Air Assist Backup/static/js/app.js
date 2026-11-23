
// ============================================================
// AIRASSIST - GEMINI RAG CHATBOT
// Connects the frontend to Flask /api/chat
// ============================================================

const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const chatStream = document.getElementById("chatStream");
const sendButton = document.getElementById("btnSendChat");

// Prevent multiple requests at the same time
let isChatLoading = false;


// ------------------------------------------------------------
// Add a message to the chat window
// ------------------------------------------------------------

function addChatMessage(message, sender, sources = []) {
    const bubble = document.createElement("div");

    bubble.className =
        sender === "user"
            ? "chat-bubble user-bubble"
            : "chat-bubble bot-bubble";

    const header = document.createElement("div");
    header.className = "bubble-header";

    const icon = document.createElement("i");
    icon.className =
        sender === "user"
            ? "fa-solid fa-user"
            : "fa-solid fa-robot";

    header.appendChild(icon);

    const headerText = document.createTextNode(
        sender === "user" ? " You" : " AirAssist AI"
    );

    header.appendChild(headerText);

    const body = document.createElement("div");
    body.className = "bubble-body";

    // textContent prevents HTML injection
    body.textContent = message;

    bubble.appendChild(header);
    bubble.appendChild(body);

    // Display knowledge-base source filenames
    if (sources.length > 0) {
        const sourceContainer = document.createElement("div");
        sourceContainer.className = "chat-sources";

        const sourceTitle = document.createElement("strong");
        sourceTitle.textContent = "Sources: ";

        sourceContainer.appendChild(sourceTitle);

        const sourceText = document.createElement("span");
        sourceText.textContent = sources.join(", ");

        sourceContainer.appendChild(sourceText);
        bubble.appendChild(sourceContainer);
    }

    chatStream.appendChild(bubble);

    // Automatically scroll to the latest message
    chatStream.scrollTop = chatStream.scrollHeight;

    return bubble;
}


// ------------------------------------------------------------
// Show loading message
// ------------------------------------------------------------

function showTypingMessage() {
    const typingBubble = document.createElement("div");

    typingBubble.className = "chat-bubble bot-bubble";
    typingBubble.id = "chatTyping";

    const header = document.createElement("div");
    header.className = "bubble-header";
    header.textContent = "AirAssist AI";

    const body = document.createElement("div");
    body.className = "bubble-body";
    body.textContent = "Analyzing your question...";

    typingBubble.appendChild(header);
    typingBubble.appendChild(body);

    chatStream.appendChild(typingBubble);
    chatStream.scrollTop = chatStream.scrollHeight;

    return typingBubble;
}


// ------------------------------------------------------------
// Send a question to Flask backend
// ------------------------------------------------------------

async function sendChatQuestion(question) {

    if (isChatLoading) {
        return;
    }

    question = question.trim();

    if (!question) {
        return;
    }

    isChatLoading = true;

    // Display user question
    addChatMessage(question, "user");

    // Clear input
    chatInput.value = "";

    // Disable button while processing
    if (sendButton) {
        sendButton.disabled = true;
        sendButton.innerHTML =
            '<i class="fa-solid fa-spinner fa-spin"></i> Thinking...';
    }

    const typingBubble = showTypingMessage();

    try {

        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question
            })
        });

        const data = await response.json();

        // Remove loading message
        typingBubble.remove();

        if (!response.ok || data.status !== "success") {
            throw new Error(
                data.answer || "Unable to get an answer from AirAssist."
            );
        }

        // Display Gemini-generated response
        addChatMessage(
            data.answer || "Sorry, no answer was generated.",
            "bot",
            data.sources || []
        );

    } catch (error) {

        console.error("AirAssist Chat Error:", error);

        typingBubble.remove();

        addChatMessage(
            "Sorry, AirAssist could not process your question. " +
            "Please check that the Flask server is running and try again.",
            "bot"
        );

    } finally {

        isChatLoading = false;

        if (sendButton) {
            sendButton.disabled = false;
            sendButton.innerHTML =
                '<i class="fa-solid fa-paper-plane"></i> Send';
        }

        chatInput.focus();
    }
}


// ------------------------------------------------------------
// Handle form submission
// ------------------------------------------------------------

function handleChatSubmit(event) {
    event.preventDefault();

    const question = chatInput.value.trim();

    sendChatQuestion(question);
}


// ------------------------------------------------------------
// Handle quick question buttons
// ------------------------------------------------------------

function sendQuickQuery(question) {
    sendChatQuestion(question);
}


// ------------------------------------------------------------
// Make functions available to HTML onclick handlers
// ------------------------------------------------------------

window.handleChatSubmit = handleChatSubmit;
window.sendQuickQuery = sendQuickQuery;
