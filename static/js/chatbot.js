document.addEventListener("DOMContentLoaded", function() {
    const chatbotBtn = document.querySelector(".chatbot-btn");
    const chatbotWindow = document.querySelector(".chatbot-window");

    if (chatbotBtn && chatbotWindow) {
        chatbotBtn.addEventListener("click", function() {
            if (chatbotWindow.style.display === "block") {
                chatbotWindow.style.display = "none";
            } else {
                chatbotWindow.style.display = "block";
            }
        });
    }
});
