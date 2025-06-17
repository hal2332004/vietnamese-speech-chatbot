// Get the record button element by its ID
const recordBtn = document.getElementById("recordBtn");
// Declare variables for the MediaRecorder and audio chunks
let mediaRecorder;
let audioChunks = [];

// Add a click event listener to the record button
recordBtn.addEventListener("click", async () => {
    // If mediaRecorder is not initialized or is inactive, start recording
    if (!mediaRecorder || mediaRecorder.state === "inactive") {
        // Request access to the user's microphone
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        // Create a new MediaRecorder instance with the audio stream
        mediaRecorder = new MediaRecorder(stream);
        // Reset the audioChunks array to store new data
        audioChunks = [];

        // When audio data is available, push it to the audioChunks array
        mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);

        // When recording stops, process the recorded audio
        mediaRecorder.onstop = async () => {
            // Create a Blob from the recorded audio chunks
            const blob = new Blob(audioChunks, { type: "audio/wav" });
            // Create a File object from the Blob
            const file = new File([blob], "input.wav", { type: "audio/wav" });

            // Prepare form data to send to the server
            const formData = new FormData();
            formData.append("file", file);

            // Send the audio file to the server endpoint via POST request
            const res = await fetch("/voicechat", { method: "POST", body: formData });
            // Parse the JSON response from the server
            const data = await res.json();

            // Display the question text returned from the server
            document.getElementById("questionText").innerText = "🗣️ " + data.question;
            // Display the answer text returned from the server
            document.getElementById("answerText").innerText = "🤖 " + data.answer;

            // Get the audio playback element and set its source to the returned audio URL
            const audio = document.getElementById("audioPlayback");
            audio.src = data.audio_url;
            audio.hidden = false;
            // Play the audio response
            audio.play();
        };

        // Start recording audio
        mediaRecorder.start();
        // Change the button text to indicate recording is in progress
        recordBtn.innerText = "⏹️ Dừng";
    } else {
        // If already recording, stop the recording
        mediaRecorder.stop();
        // Change the button text back to indicate ready to record
        recordBtn.innerText = "🎤 Ghi âm";
    }
});