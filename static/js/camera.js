document.addEventListener("DOMContentLoaded", () => {

    // ============================================================
    // ELEMENTS
    // ============================================================

    const cameraButton =
        document.getElementById("cameraButton");

    const cameraSection =
        document.getElementById("cameraSection");

    const video =
        document.getElementById("video");

    const canvas =
        document.getElementById("canvas");

    const cameraStatus =
        document.getElementById("cameraStatus");

    const moodResult =
        document.getElementById("moodResult");

    const detectedMood =
        document.getElementById("detectedMood");

    const confidence =
        document.getElementById("confidence");

    const languageSection =
        document.getElementById("languageSection");

    const languageSelect =
        document.getElementById("language");

    const songsContainer =
        document.getElementById("songsContainer");

    const voiceButton =
        document.getElementById("voiceButton");

    let stream = null;
    let currentMood = "";


    // ============================================================
    // CAMERA DETECTION
    // ============================================================

    if (cameraButton) {

        cameraButton.addEventListener("click", async () => {

            cameraSection.style.display = "block";

            try {

                stream =
                    await navigator.mediaDevices.getUserMedia({
                        video: true,
                        audio: false
                    });

                video.srcObject = stream;

                cameraStatus.innerHTML =
                    "📷 Camera is ready!";


                // Remove old capture button
                const oldButton =
                    document.getElementById("captureMoodButton");

                if (oldButton) {
                    oldButton.remove();
                }


                // Create Capture button
                const captureButton =
                    document.createElement("button");

                captureButton.id =
                    "captureMoodButton";

                captureButton.className =
                    "main-btn";

                captureButton.innerHTML =
                    "📸 Capture My Mood";

                captureButton.style.marginTop =
                    "20px";


                cameraSection
                    .querySelector(".camera-box")
                    .appendChild(captureButton);


                captureButton.addEventListener(
                    "click",
                    captureMood
                );


            } catch (error) {

                console.error(error);

                cameraStatus.innerHTML =
                    "❌ Camera access denied. Please allow camera permission.";

            }

        });

    }


    // ============================================================
    // CAPTURE IMAGE + DETECT MOOD
    // ============================================================

    async function captureMood() {

        if (
            !video ||
            !video.videoWidth ||
            !video.videoHeight
        ) {

            cameraStatus.innerHTML =
                "❌ Camera is not ready. Please wait.";

            return;
        }


        cameraStatus.innerHTML =
            "🤖 Analyzing your mood...";


        canvas.width =
            video.videoWidth;

        canvas.height =
            video.videoHeight;


        const context =
            canvas.getContext("2d");


        context.drawImage(
            video,
            0,
            0,
            canvas.width,
            canvas.height
        );


        canvas.toBlob(
            async (blob) => {

                if (!blob) {

                    cameraStatus.innerHTML =
                        "❌ Could not capture image.";

                    return;
                }


                const formData =
                    new FormData();


                formData.append(
                    "image",
                    blob,
                    "mood.jpg"
                );


                try {

                    const response =
                        await fetch(
                            "/analyze-emotion",
                            {
                                method: "POST",
                                body: formData
                            }
                        );


                    const data =
                        await response.json();


                    console.log(
                        "Emotion result:",
                        data
                    );


                    if (data.success) {

                        currentMood =
                            data.emotion.toLowerCase();


                        detectedMood.textContent =
                            capitalize(currentMood);


                        confidence.textContent =
                            `${Number(
                                data.confidence
                            ).toFixed(2)}%`;


                        moodResult.style.display =
                            "block";


                        languageSection.style.display =
                            "block";


                        songsContainer.innerHTML =
                            "";


                        cameraStatus.innerHTML =
                            "✅ Mood detected successfully!";


                        // Stop camera
                        if (stream) {

                            stream
                                .getTracks()
                                .forEach(track => {
                                    track.stop();
                                });

                            video.srcObject = null;
                        }


                        languageSection.scrollIntoView({
                            behavior: "smooth",
                            block: "center"
                        });


                    } else {

                        cameraStatus.innerHTML =
                            "❌ " +
                            (
                                data.error ||
                                "Could not detect mood."
                            );
                    }


                } catch (error) {

                    console.error(
                        "Emotion detection error:",
                        error
                    );


                    cameraStatus.innerHTML =
                        "❌ Something went wrong while detecting mood.";

                }

            },
            "image/jpeg",
            0.9
        );

    }


    // ============================================================
    // 🎤 VOICE EMOTION DETECTION
    // ============================================================

    let audioContext = null;
    let audioStream = null;
    let audioProcessor = null;
    let audioSource = null;

    let audioChunks = [];

    let isRecording = false;

    let recordingTimer = null;
    let recordingSeconds = 0;


    if (voiceButton) {

        voiceButton.addEventListener(
            "click",
            startVoiceDetection
        );

    }


    // ============================================================
    // START VOICE DETECTION
    // ============================================================

    async function startVoiceDetection() {

        if (isRecording) {
            return;
        }


        try {

            // Request microphone
            audioStream =
                await navigator.mediaDevices
                    .getUserMedia({
                        audio: true
                    });


            // Create AudioContext
            audioContext =
                new (
                    window.AudioContext ||
                    window.webkitAudioContext
                )();


            audioSource =
                audioContext.createMediaStreamSource(
                    audioStream
                );


            audioProcessor =
                audioContext.createScriptProcessor(
                    4096,
                    1,
                    1
                );


            audioChunks = [];

            isRecording = true;

            recordingSeconds = 0;


            voiceButton.innerHTML =
                "🔴 Recording... 0s";

            voiceButton.style.background =
                "#dc2626";


            // Capture microphone samples
            audioProcessor.onaudioprocess =
                function (event) {

                    if (!isRecording) {
                        return;
                    }


                    const inputData =
                        event.inputBuffer
                            .getChannelData(0);


                    audioChunks.push(
                        new Float32Array(inputData)
                    );

                };


            audioSource.connect(
                audioProcessor
            );


            audioProcessor.connect(
                audioContext.destination
            );


            // Timer
            recordingTimer =
                setInterval(() => {

                    recordingSeconds++;


                    voiceButton.innerHTML =
                        `🔴 Recording... ${recordingSeconds}s`;


                    // Stop after 6 seconds
                    if (
                        recordingSeconds >= 6
                    ) {

                        stopVoiceRecording();

                    }

                }, 1000);


            console.log(
                "🎤 Voice recording started"
            );


        } catch (error) {

            console.error(
                "Microphone error:",
                error
            );


            voiceButton.innerHTML =
                "🎤 Use My Voice";


            voiceButton.style.background =
                "#334155";


            alert(
                "❌ Microphone access was denied. Please allow microphone permission."
            );

        }

    }


    // ============================================================
    // STOP VOICE RECORDING
    // ============================================================

    async function stopVoiceRecording() {

        if (!isRecording) {
            return;
        }


        isRecording = false;


        clearInterval(
            recordingTimer
        );


        voiceButton.innerHTML =
            "🤖 Analyzing Voice...";

        voiceButton.disabled =
            true;


        // Disconnect audio
        if (audioProcessor) {
            audioProcessor.disconnect();
        }


        if (audioSource) {
            audioSource.disconnect();
        }


        // Stop microphone
        if (audioStream) {

            audioStream
                .getTracks()
                .forEach(track => {
                    track.stop();
                });

        }


        // IMPORTANT:
        // Save the real microphone sample rate
        const sampleRate =
            audioContext
                ? audioContext.sampleRate
                : 44100;


        // Close AudioContext
        if (audioContext) {

            await audioContext.close();

        }


        // Convert chunks to WAV
        const wavBlob =
            createWavBlob(
                audioChunks,
                sampleRate
            );


        // Send voice to Flask
        await sendVoiceToServer(
            wavBlob
        );


        voiceButton.disabled =
            false;


        voiceButton.innerHTML =
            "🎤 Use My Voice";


        voiceButton.style.background =
            "#334155";

    }


    // ============================================================
    // CREATE WAV FILE
    // ============================================================

    function createWavBlob(
        chunks,
        sampleRate
    ) {

        let totalLength = 0;


        chunks.forEach(chunk => {

            totalLength +=
                chunk.length;

        });


        const samples =
            new Float32Array(
                totalLength
            );


        let offset = 0;


        chunks.forEach(chunk => {

            samples.set(
                chunk,
                offset
            );

            offset +=
                chunk.length;

        });


        const buffer =
            new ArrayBuffer(
                44 +
                samples.length * 2
            );


        const view =
            new DataView(buffer);


        // WAV header
        writeString(
            view,
            0,
            "RIFF"
        );


        view.setUint32(
            4,
            36 +
            samples.length * 2,
            true
        );


        writeString(
            view,
            8,
            "WAVE"
        );


        writeString(
            view,
            12,
            "fmt "
        );


        view.setUint32(
            16,
            16,
            true
        );


        // PCM
        view.setUint16(
            20,
            1,
            true
        );


        // Mono
        view.setUint16(
            22,
            1,
            true
        );


        view.setUint32(
            24,
            sampleRate,
            true
        );


        view.setUint32(
            28,
            sampleRate * 2,
            true
        );


        view.setUint16(
            32,
            2,
            true
        );


        view.setUint16(
            34,
            16,
            true
        );


        writeString(
            view,
            36,
            "data"
        );


        view.setUint32(
            40,
            samples.length * 2,
            true
        );


        // Convert Float32 → PCM16
        let index = 44;


        for (
            let i = 0;
            i < samples.length;
            i++
        ) {

            let sample =
                Math.max(
                    -1,
                    Math.min(
                        1,
                        samples[i]
                    )
                );


            sample =
                sample < 0
                    ? sample * 0x8000
                    : sample * 0x7fff;


            view.setInt16(
                index,
                sample,
                true
            );


            index += 2;

        }


        return new Blob(
            [view],
            {
                type: "audio/wav"
            }
        );

    }


    // ============================================================
    // WRITE WAV STRING
    // ============================================================

    function writeString(
        view,
        offset,
        string
    ) {

        for (
            let i = 0;
            i < string.length;
            i++
        ) {

            view.setUint8(
                offset + i,
                string.charCodeAt(i)
            );

        }

    }


    // ============================================================
    // SEND VOICE TO FLASK
    // ============================================================

    async function sendVoiceToServer(
        wavBlob
    ) {

        try {

            const formData =
                new FormData();


            formData.append(
                "audio",
                wavBlob,
                "voice.wav"
            );


            console.log(
                "🎤 Sending voice to Flask..."
            );


            const response =
                await fetch(
                    "/analyze-voice",
                    {
                        method: "POST",
                        body: formData
                    }
                );


            const data =
                await response.json();


            console.log(
                "🎤 Voice emotion result:",
                data
            );


            if (data.success) {

                // IMPORTANT:
                // Voice uses the SAME currentMood
                // as face detection.
                currentMood =
                    data.emotion.toLowerCase();


                detectedMood.textContent =
                    capitalize(currentMood);


                confidence.textContent =
                    `${Number(
                        data.confidence
                    ).toFixed(2)}%`;


                moodResult.style.display =
                    "block";


                languageSection.style.display =
                    "block";


                songsContainer.innerHTML =
                    "";


                languageSection.scrollIntoView({
                    behavior: "smooth",
                    block: "center"
                });


                alert(
                    `🎤 Voice emotion detected: ${capitalize(currentMood)}`
                );


            } else {

                alert(
                    "❌ " +
                    (
                        data.error ||
                        "Could not detect voice emotion."
                    )
                );

            }


        } catch (error) {

            console.error(
                "Voice analysis error:",
                error
            );


            alert(
                "❌ Could not connect to voice emotion analyzer."
            );

        }

    }


    // ============================================================
    // GET MUSIC RECOMMENDATIONS
    // ============================================================

    window.getRecommendations =
        async function () {

            console.log(
                "🎵 getRecommendations() started"
            );


            if (!currentMood) {

                alert(
                    "Please detect your mood first."
                );

                return;
            }


            const language =
                languageSelect.value;


            console.log(
                "😊 Mood:",
                currentMood
            );


            console.log(
                "🌐 Language:",
                language
            );


            if (!language) {

                alert(
                    "Please select a language."
                );

                return;
            }


            songsContainer.innerHTML = `
                <div class="loading">
                    🎵 Finding songs for your mood...
                </div>
            `;


            try {

                const response =
                    await fetch(
                        `/recommendations/${encodeURIComponent(currentMood)}?language=${encodeURIComponent(language)}`
                    );


                const data =
                    await response.json();


                console.log(
                    "🎵 Recommendation response:",
                    data
                );


                if (
                    data.success &&
                    data.songs &&
                    data.songs.length > 0
                ) {

                    displaySongs(
                        data.songs,
                        data.mood,
                        data.language
                    );


                } else {

                    songsContainer.innerHTML = `
                        <div class="no-songs">
                            😕 No songs found for this mood and language.
                        </div>
                    `;

                }


            } catch (error) {

                console.error(
                    "❌ Recommendation error:",
                    error
                );


                songsContainer.innerHTML = `
                    <div class="no-songs">
                        ❌ Could not load recommendations.
                    </div>
                `;

            }

        };


    // ============================================================
    // GET MY SONGS BUTTON
    // ============================================================

    const recommendButton =
        document.getElementById(
            "recommendButton"
        );


    if (recommendButton) {

        recommendButton.addEventListener(
            "click",
            () => {

                console.log(
                    "🎵 Get My Songs clicked"
                );

                window.getRecommendations();

            }
        );

    }


    // ============================================================
    // DISPLAY SONGS
    // ============================================================

    function displaySongs(
        songs,
        mood,
        language
    ) {

        let html = `

            <div class="recommendation-header">

                <h2>
                    🎵 Songs For Your Mood
                </h2>

                <p>

                    Mood:

                    <strong>
                        ${capitalize(mood)}
                    </strong>

                    &nbsp; • &nbsp;

                    Language:

                    <strong>
                        ${capitalize(language)}
                    </strong>

                </p>

            </div>


            <div class="songs-grid">

        `;


        songs.forEach(
            (song, index) => {

                html += `

                    <div class="song-card">

                        <div class="song-number">

                            ${index + 1}

                        </div>


                        <div class="song-info">

                            <h3>

                                ${escapeHTML(
                                    song.title
                                )}

                            </h3>


                            <p>

                                ${escapeHTML(
                                    song.artist
                                )}

                            </p>

                        </div>


                        <button
                            class="play-song-btn"
                            onclick="window.playSong('${escapeAttribute(song.youtube_url)}')"
                        >

                            ▶ Play Song

                        </button>


                        <button
                            class="youtube-btn"
                            onclick="window.openYouTube('${escapeAttribute(song.youtube_url)}')"
                        >

                            🔗 YouTube

                        </button>


                    </div>

                `;

            }
        );


        html += `

            </div>

        `;


        songsContainer.innerHTML =
            html;


        songsContainer.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    }


    // ============================================================
    // PLAY SONG
    // ============================================================

    window.playSong =
        function (youtubeURL) {

            if (!youtubeURL) {

                alert(
                    "YouTube video is not available."
                );

                return;
            }


            const confirmRedirect =
                confirm(
                    "🎵 Do you want to open this song on YouTube?"
                );


            if (confirmRedirect) {

                window.open(
                    youtubeURL,
                    "_blank",
                    "noopener,noreferrer"
                );

            }

        };


  // ============================================================
// OPEN YOUTUBE IN GOOGLE CHROME
// ============================================================

async function redirectToYouTube(youtubeURL) {

    if (!youtubeURL) {

        alert("YouTube video is not available.");

        return;
    }

    const confirmRedirect = confirm(
        "🎵 Do you want to open this song on YouTube?"
    );

    if (!confirmRedirect) {
        return;
    }

    try {

        const response = await fetch(
            `/open-youtube?url=${encodeURIComponent(youtubeURL)}`
        );

        const data = await response.json();

        if (!data.success) {

            alert(
                "❌ Could not open YouTube:\n" +
                (data.error || "Unknown error")
            );

        }

    } catch (error) {

        console.error(
            "YouTube redirect error:",
            error
        );

        alert(
            "❌ Could not open YouTube."
        );

    }
}


// ============================================================
// PLAY SONG
// ============================================================

window.playSong = function (youtubeURL) {

    redirectToYouTube(youtubeURL);

};


// ============================================================
// OPEN YOUTUBE
// ============================================================

window.openYouTube = function (youtubeURL) {

    redirectToYouTube(youtubeURL);

};


    // ============================================================
    // CAPITALIZE
    // ============================================================

    function capitalize(text) {

        if (!text) {
            return "";
        }


        return (
            text.charAt(0).toUpperCase() +
            text.slice(1)
        );

    }


    // ============================================================
    // SECURITY HELPERS
    // ============================================================

    function escapeHTML(text) {

        if (
            text === undefined ||
            text === null
        ) {

            return "";

        }


        return String(text)
            .replace(
                /&/g,
                "&amp;"
            )
            .replace(
                /</g,
                "&lt;"
            )
            .replace(
                />/g,
                "&gt;"
            )
            .replace(
                /"/g,
                "&quot;"
            )
            .replace(
                /'/g,
                "&#039;"
            );

    }


    function escapeAttribute(text) {

        if (!text) {
            return "";
        }


        return String(text)
            .replace(
                /\\/g,
                "\\\\"
            )
            .replace(
                /'/g,
                "\\'"
            );

    }

});