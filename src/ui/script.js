document.addEventListener('DOMContentLoaded', () => {
    // --- DOM ELEMENTS ---
    const chatList = document.getElementById('chatList');
    const newChatBtn = document.getElementById('newChatBtn');
    const deleteCurrentChatBtn = document.getElementById('deleteCurrentChatBtn');
    const chatContainer = document.getElementById('chatContainer');
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    const audioUploadBtn = document.getElementById('audioUploadBtn');
    const audioFile = document.getElementById('audioFile');
    const uploadInfo = document.getElementById('uploadInfo');
    const recordBtn = document.getElementById('recordBtn');
    const chatTitle = document.getElementById('chatTitle');

    // --- APP STATE & DATA ---
    let appData = {
        activeConversationId: null,
        conversations: {}
    };
    
    let isProcessing = false;
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;
    let mediaStream = null;

    // --- INITIALIZATION ---
    loadData();
    renderSidebar();
    renderActiveConversation();
    updateUIStates();

    // --- EVENT LISTENERS ---
    newChatBtn.addEventListener('click', createNewConversation);
    deleteCurrentChatBtn.addEventListener('click', deleteCurrentConversation);
    messageInput.addEventListener('input', () => { updateUIStates(); autoResize(); });
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
    audioUploadBtn.addEventListener('click', () => audioFile.click());
    audioFile.addEventListener('change', handleAudioUpload);
    recordBtn.addEventListener('click', toggleRecording);
    
    // Event delegation for dynamically created chat list items
    chatList.addEventListener('click', (e) => {
        const target = e.target;
        if (target.closest('.delete-chat-btn')) {
            const conversationId = target.closest('.chat-list-item').dataset.id;
            deleteConversation(conversationId);
        } else if (target.closest('.chat-list-item')) {
            const conversationId = target.closest('.chat-list-item').dataset.id;
            switchConversation(conversationId);
        }
    });

    // --- DATA MANAGEMENT ---
    function saveData() {
        localStorage.setItem('voiceAssistantData', JSON.stringify(appData));
    }

    function loadData() {
        const savedData = localStorage.getItem('voiceAssistantData');
        if (savedData) {
            appData = JSON.parse(savedData);
        }
        // If no active conversation or it points to a non-existent one, handle it
        if (!appData.activeConversationId || !appData.conversations[appData.activeConversationId]) {
            if (Object.keys(appData.conversations).length > 0) {
                appData.activeConversationId = Object.keys(appData.conversations)[0];
            } else {
                appData.activeConversationId = null;
            }
        }
    }

    // --- RENDERING ---
    function renderSidebar() {
        chatList.innerHTML = '';
        const sortedIds = Object.keys(appData.conversations).sort((a, b) => b - a); // Sort by timestamp ID
        sortedIds.forEach(id => {
            const conv = appData.conversations[id];
            const li = document.createElement('li');
            li.className = `chat-list-item ${id === appData.activeConversationId ? 'active' : ''}`;
            li.dataset.id = id;
            li.textContent = conv.title;
            li.innerHTML = `
                <span class="chat-item-title">${conv.title}</span>
                <button class="delete-chat-btn" title="Xóa cuộc trò chuyện">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/><path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/></svg>
                </button>`;
            chatList.appendChild(li);
        });
    }

    function renderActiveConversation() {
        chatContainer.innerHTML = '';
        if (appData.activeConversationId && appData.conversations[appData.activeConversationId]) {
            const activeConv = appData.conversations[appData.activeConversationId];
            chatTitle.textContent = activeConv.title;
            if (activeConv.messages.length === 0) {
                 renderWelcomeMessage();
            } else {
                activeConv.messages.forEach(msg => renderMessage(msg.type, msg.content));
            }
        } else {
            renderWelcomeMessage();
            chatTitle.textContent = "🎙️ Voice Assistant";
        }
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    function renderMessage(type, content) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}`;
        messageElement.innerHTML = `
            <div class="avatar ${type}">${type === 'user' ? 'U' : 'AI'}</div>
            <div class="message-content">${content}</div>`;
        chatContainer.appendChild(messageElement);
    }
    
    function renderWelcomeMessage() {
         chatContainer.innerHTML = `
            <div class="welcome-message">
                <h2>Bắt đầu cuộc trò chuyện mới</h2>
                <p>Tải lên file âm thanh, ghi âm hoặc nhập tin nhắn để bắt đầu.</p>
            </div>`;
    }

    // --- CONVERSATION MANAGEMENT ---
    function createNewConversation() {
        const newId = Date.now().toString();
        appData.conversations[newId] = {
            id: newId,
            title: 'Cuộc trò chuyện mới',
            messages: []
        };
        appData.activeConversationId = newId;
        saveData();
        renderSidebar();
        renderActiveConversation();
        updateUIStates();
    }
    
    function switchConversation(id) {
        if (appData.activeConversationId === id) return;
        appData.activeConversationId = id;
        saveData();
        renderSidebar();
        renderActiveConversation();
        updateUIStates();
    }

    function deleteConversation(id) {
        if (!confirm(`Bạn có chắc muốn xóa cuộc trò chuyện "${appData.conversations[id].title}" không?`)) return;
        
        delete appData.conversations[id];
        
        if (appData.activeConversationId === id) {
             const remainingIds = Object.keys(appData.conversations).sort((a,b) => b-a);
             appData.activeConversationId = remainingIds.length > 0 ? remainingIds[0] : null;
        }

        saveData();
        renderSidebar();
        renderActiveConversation();
        updateUIStates();
    }
    
    function deleteCurrentConversation() {
        if (appData.activeConversationId) {
            deleteConversation(appData.activeConversationId);
        } else {
            alert("Không có cuộc trò chuyện nào để xóa.");
        }
    }
    
    function addMessage(type, content) {
        if (!appData.activeConversationId) {
            createNewConversation();
        }

        const activeConv = appData.conversations[appData.activeConversationId];

        if (activeConv.messages.length === 0) {
            chatContainer.innerHTML = '';
        }

        const message = { type, content, timestamp: new Date().toISOString() };
        activeConv.messages.push(message);

        // Auto-title conversation on first user message
        if (activeConv.messages.length === 1 && type === 'user') {
            const textContent = new DOMParser().parseFromString(content, 'text/html').body.textContent || content;
            const newTitle = textContent.substring(0, 30) + (textContent.length > 30 ? '...' : '');
            
            if (activeConv.title !== newTitle) {
                activeConv.title = newTitle;
                chatTitle.textContent = newTitle; 
                renderSidebar(); 
            }
        }

        renderMessage(type, content);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        saveData();
    }
    
    // --- UI & INTERACTIONS ---
    function updateUIStates() {
        const hasContent = messageInput.value.trim().length > 0;
        const hasActiveChat = !!appData.activeConversationId;
        sendBtn.disabled = !hasContent || isProcessing || isRecording;
        messageInput.disabled = isRecording;
        recordBtn.disabled = isProcessing;
        audioUploadBtn.disabled = isProcessing || isRecording;
        deleteCurrentChatBtn.disabled = !hasActiveChat;
    }

    function autoResize() {
        messageInput.style.height = 'auto';
        messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
    }

    function sendMessage() {
        const content = messageInput.value.trim();
        if (content && !isProcessing && !isRecording) {
            addMessage('user', content);
            messageInput.value = '';
            autoResize();
            // Placeholder for AI response
        }
    }
    
    // --- AUDIO HANDLING (Unchanged logic, just integrated) ---
    function handleAudioUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        if (!file.type.startsWith('audio/')) { alert('Vui lòng chọn file âm thanh hợp lệ'); return; }
        displayAudioMessage(file);
        processAudioFile(file);
        audioFile.value = '';
    }
    
    async function toggleRecording() {
        if (isRecording) stopRecording();
        else await startRecording();
    }

    async function startRecording() {
        try {
            mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            isRecording = true;
            audioChunks = [];
            mediaRecorder = new MediaRecorder(mediaStream);
            mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const fileName = `recording-${Date.now()}.webm`;
                const recordedFile = new File([audioBlob], fileName, { type: 'audio/webm' });
                displayAudioMessage(recordedFile);
                processAudioFile(recordedFile);
                mediaStream.getTracks().forEach(track => track.stop());
            };
            mediaRecorder.start();
            updateRecordingUI(true);
        } catch (err) {
            alert("Không thể truy cập micro. Vui lòng cấp quyền.");
        }
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== "inactive") {
            mediaRecorder.stop();
            isRecording = false;
            updateRecordingUI(false);
        }
    }
    
    function updateRecordingUI(recording) {
        isRecording = recording;
        recordBtn.textContent = recording ? '🛑 Dừng' : '🎙️ Ghi Âm';
        recordBtn.classList.toggle('recording', recording);
        uploadInfo.textContent = recording ? '🔴 Đang ghi âm...' : 'Chọn file hoặc bắt đầu ghi âm';
        updateUIStates();
    }

    function displayAudioMessage(file) {
        const audioHTML = `<div class="audio-message"><div class="audio-icon">🎵</div><div class="audio-info"><div class="audio-name">${file.name}</div><div class="audio-size">${(file.size / 1024 / 1024).toFixed(2)} MB</div></div></div>`;
        addMessage('user', audioHTML);
    }
    
    function processAudioFile(file) {
        console.log("Processing audio file:", file.name);
        // This is where you would send the file to a server for speech-to-text
    }
});