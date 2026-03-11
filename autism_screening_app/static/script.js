// autism_screening_app/static/script.js
// Client-side logic for webcam capture, behavioral tests, and results dashboard

document.addEventListener('DOMContentLoaded', () => {
    // ===========================================================================
    // DOM REFERENCES
    // ===========================================================================
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const htmlElement = document.documentElement;
    const themeIcon = themeToggleBtn ? themeToggleBtn.querySelector('i') : null;
    const THEME_KEY = 'themePreferenceAutismScreening';

    const startSessionBtn = document.getElementById('startSessionBtn');
    const sessionInfo = document.getElementById('sessionInfo');
    const sessionIdDisplay = document.getElementById('sessionIdDisplay');
    const webcamSection = document.getElementById('webcamSection');
    const startCamBtn = document.getElementById('startCamBtn');
    const stopCamBtn = document.getElementById('stopCamBtn');
    const webcamVideo = document.getElementById('webcamVideo');
    const overlayCanvas = document.getElementById('overlayCanvas');
    const webcamStatus = document.getElementById('webcamStatus');
    const testPanels = document.getElementById('testPanels');
    const testInstructions = document.getElementById('testInstructions');
    const analyzeSection = document.getElementById('analyzeSection');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const analyzeLoading = document.getElementById('analyzeLoading');
    const resultsDashboard = document.getElementById('resultsDashboard');
    const errorArea = document.getElementById('errorArea');

    // Test buttons
    const startGazeTest = document.getElementById('startGazeTest');
    const startExpressionTest = document.getElementById('startExpressionTest');
    const startHeadTest = document.getElementById('startHeadTest');
    const startReactionTest = document.getElementById('startReactionTest');

    // ===========================================================================
    // STATE
    // ===========================================================================
    let sessionId = null;
    let webcamStream = null;
    let captureCanvas = document.createElement('canvas');
    let captureCtx = captureCanvas.getContext('2d');
    let overlayCtx = overlayCanvas ? overlayCanvas.getContext('2d') : null;
    let activeTest = null;
    let testInterval = null;
    let frameCount = 0;
    const FRAMES_PER_TEST = 30;
    const FRAME_INTERVAL_MS = 500;
    let completedTests = new Set();

    // Emotion test state
    const EMOTIONS = [
        { name: 'happy', emoji: '😊', instruction: 'SMILE widely!' },
        { name: 'sad', emoji: '😢', instruction: 'Look SAD and frown' },
        { name: 'angry', emoji: '😠', instruction: 'Show ANGER — furrow your brows' },
        { name: 'surprised', emoji: '😲', instruction: 'Look SURPRISED — open eyes wide' }
    ];
    let currentEmotionIndex = 0;

    // Stimulus test state
    const SHAPES = ['circle', 'square', 'triangle', 'star'];
    const SHAPE_COLORS = ['#ff3838', '#3b82f6', '#10b981', '#f59e0b'];

    // Audio context for sound stimuli
    let audioCtx = null;
    function getAudioCtx() {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        return audioCtx;
    }

    // Play a beep sound for stimulus reaction
    function playBeep(frequency = 600, duration = 150) {
        try {
            const ctx = getAudioCtx();
            const oscillator = ctx.createOscillator();
            const gainNode = ctx.createGain();
            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(frequency, ctx.currentTime);
            gainNode.gain.setValueAtTime(0.3, ctx.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration / 1000);
            oscillator.connect(gainNode);
            gainNode.connect(ctx.destination);
            oscillator.start();
            oscillator.stop(ctx.currentTime + duration / 1000);
        } catch (e) {
            // Audio not supported — ignore
        }
    }

    // Chart instances (for cleanup)
    let chartInstances = {};

    // ===========================================================================
    // THEME TOGGLE (matching existing pattern)
    // ===========================================================================
    function applyTheme(theme) {
        if (theme === 'dark') {
            htmlElement.setAttribute('data-theme', 'dark');
            if (themeIcon) { themeIcon.classList.remove('fa-sun'); themeIcon.classList.add('fa-moon'); }
        } else {
            htmlElement.removeAttribute('data-theme');
            if (themeIcon) { themeIcon.classList.remove('fa-moon'); themeIcon.classList.add('fa-sun'); }
        }
    }
    function saveThemePreference(theme) { localStorage.setItem(THEME_KEY, theme); }
    function loadThemePreference() {
        const saved = localStorage.getItem(THEME_KEY);
        if (saved) return saved;
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    if (themeToggleBtn) {
        applyTheme(loadThemePreference());
        themeToggleBtn.addEventListener('click', () => {
            const current = htmlElement.hasAttribute('data-theme') ? 'dark' : 'light';
            const next = current === 'dark' ? 'light' : 'dark';
            applyTheme(next);
            saveThemePreference(next);
        });
    }
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem(THEME_KEY)) applyTheme(e.matches ? 'dark' : 'light');
    });

    // Footer year
    const currentYearSpan = document.getElementById('currentYear');
    if (currentYearSpan) currentYearSpan.textContent = new Date().getFullYear();

    // ===========================================================================
    // UTILITY FUNCTIONS
    // ===========================================================================
    function showError(msg) {
        if (errorArea) { errorArea.textContent = msg; errorArea.classList.remove('hidden'); }
    }
    function clearError() {
        if (errorArea) { errorArea.textContent = ''; errorArea.classList.add('hidden'); }
    }

    function setTestStatus(testId, msg) {
        const el = document.getElementById(testId + 'Status');
        if (el) el.textContent = msg;
    }

    function updateProgress(testId, percent) {
        const fill = document.getElementById(testId + 'ProgressFill');
        const text = document.getElementById(testId + 'ProgressText');
        if (fill) fill.style.width = percent + '%';
        if (text) text.textContent = Math.round(percent) + '%';
    }

    // ===========================================================================
    // SESSION MANAGEMENT
    // ===========================================================================
    if (startSessionBtn) {
        startSessionBtn.addEventListener('click', async () => {
            clearError();
            startSessionBtn.disabled = true;
            startSessionBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
            try {
                const res = await fetch('/autism-screening/api/start-session', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({})
                });
                if (!res.ok) throw new Error((await res.json()).detail || 'Failed to start session');
                const data = await res.json();
                sessionId = data.session_id;
                sessionIdDisplay.textContent = sessionId;
                sessionInfo.classList.remove('hidden');
                webcamSection.classList.remove('hidden');
                startSessionBtn.innerHTML = '<i class="fas fa-check-circle"></i> Session Active';
            } catch (err) {
                showError('Failed to start session: ' + err.message);
                startSessionBtn.disabled = false;
                startSessionBtn.innerHTML = '<i class="fas fa-play-circle"></i> Start Screening Session';
            }
        });
    }

    // ===========================================================================
    // WEBCAM
    // ===========================================================================
    if (startCamBtn) {
        startCamBtn.addEventListener('click', async () => {
            clearError();
            try {
                webcamStream = await navigator.mediaDevices.getUserMedia({
                    video: { width: 640, height: 480, facingMode: 'user' }
                });
                webcamVideo.srcObject = webcamStream;
                startCamBtn.classList.add('hidden');
                stopCamBtn.classList.remove('hidden');
                webcamStatus.textContent = 'Camera active';
                testPanels.classList.remove('hidden');
            } catch (err) {
                showError('Could not access webcam: ' + err.message);
            }
        });
    }

    if (stopCamBtn) {
        stopCamBtn.addEventListener('click', () => { stopWebcam(); });
    }

    function stopWebcam() {
        if (webcamStream) {
            webcamStream.getTracks().forEach(t => t.stop());
            webcamStream = null;
        }
        webcamVideo.srcObject = null;
        startCamBtn.classList.remove('hidden');
        stopCamBtn.classList.add('hidden');
        webcamStatus.textContent = 'Camera stopped';
        stopActiveTest();
    }

    // ===========================================================================
    // FRAME CAPTURE & SEND
    // ===========================================================================
    function captureFrame() {
        if (!webcamVideo || !webcamVideo.videoWidth) return null;
        captureCanvas.width = webcamVideo.videoWidth;
        captureCanvas.height = webcamVideo.videoHeight;
        captureCtx.drawImage(webcamVideo, 0, 0);
        return captureCanvas.toDataURL('image/jpeg', 0.6);
    }

    async function sendFrame(testType, extraData = {}) {
        const frameBase64 = captureFrame();
        if (!frameBase64 || !sessionId) return null;

        const payload = {
            session_id: sessionId,
            frame_base64: frameBase64,
            test_type: testType,
            timestamp: Date.now(),
            ...extraData
        };

        try {
            const res = await fetch('/autism-screening/api/process-frame', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                console.warn('Frame processing error:', errData.detail || res.status);
                return null;
            }
            return await res.json();
        } catch (err) {
            console.warn('Frame send error:', err.message);
            return null;
        }
    }

    // ===========================================================================
    // TEST MANAGEMENT
    // ===========================================================================
    function stopActiveTest() {
        if (testInterval) { clearInterval(testInterval); testInterval = null; }
        // Clear overlay canvas
        if (overlayCtx && overlayCanvas) {
            overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
        }
        // Hide test-specific stimulus UIs
        const emotionStimulus = document.getElementById('emotionStimulus');
        const stimulusDisplay = document.getElementById('stimulusDisplay');
        if (emotionStimulus) emotionStimulus.classList.add('hidden');
        if (stimulusDisplay) stimulusDisplay.classList.add('hidden');
        activeTest = null;
    }

    function markTestComplete(testName) {
        completedTests.add(testName);
        const cardMap = {
            'eye_gaze': 'testCardGaze',
            'facial_expression': 'testCardExpression',
            'head_movement': 'testCardHead',
            'reaction_stimulus': 'testCardReaction'
        };
        const card = document.getElementById(cardMap[testName]);
        if (card) { card.classList.remove('active'); card.classList.add('completed'); }
        if (completedTests.size >= 1) {
            analyzeSection.classList.remove('hidden');
        }
    }

    /**
     * Core test runner. Captures frames at intervals and sends to backend.
     * @param {string} testType - The test type key
     * @param {Function|null} getExtraData - Returns extra payload data per frame
     * @param {Function|null} onFrame - Callback with frame result
     * @param {Function|null} onStart - Called AFTER stopActiveTest, to show stimulus UI
     */
    function startTestCapture(testType, getExtraData, onFrame, onStart) {
        if (!webcamStream) { showError('Please start the webcam first.'); return; }

        // 1) Stop any active test (this hides all stimulus UIs)
        stopActiveTest();

        // 2) NOW show stimuli for this test (after stopActiveTest cleared them)
        if (onStart) onStart();

        activeTest = testType;
        frameCount = 0;

        // Progress bar ID mapping
        const progressId = {
            'eye_gaze': 'gaze',
            'facial_expression': 'expression',
            'head_movement': 'head',
            'reaction_stimulus': 'reaction'
        }[testType];
        const progressEl = document.getElementById(progressId + 'Progress');
        if (progressEl) progressEl.classList.remove('hidden');

        // Mark card active
        document.querySelectorAll('.test-card').forEach(c => c.classList.remove('active'));
        const cardMap = {
            'eye_gaze': 'testCardGaze',
            'facial_expression': 'testCardExpression',
            'head_movement': 'testCardHead',
            'reaction_stimulus': 'testCardReaction'
        };
        const card = document.getElementById(cardMap[testType]);
        if (card) card.classList.add('active');

        // Disable the test button
        const btn = document.querySelector(`[data-test="${testType}"]`);
        if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...'; }

        testInterval = setInterval(async () => {
            if (frameCount >= FRAMES_PER_TEST) {
                stopActiveTest();
                if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-check"></i> Completed'; }
                setTestStatus(progressId, 'Test completed ✓');
                markTestComplete(testType);
                return;
            }

            const extra = getExtraData ? getExtraData(frameCount) : {};
            const result = await sendFrame(testType, extra);
            frameCount++;

            const pct = (frameCount / FRAMES_PER_TEST) * 100;
            updateProgress(progressId, pct);

            if (result && onFrame) onFrame(result, frameCount);
            if (result) setTestStatus(progressId, result.message || `Frame ${frameCount}/${FRAMES_PER_TEST}`);
        }, FRAME_INTERVAL_MS);
    }

    // ===========================================================================
    // TEST 1: EYE GAZE TRACKING
    // ===========================================================================
    if (startGazeTest) {
        startGazeTest.addEventListener('click', () => {
            testInstructions.textContent = 'Follow the RED DOT with your eyes. Keep your head still.';

            startTestCapture('eye_gaze',
                // getExtraData: moving dot
                (frameIdx) => {
                    const t = frameIdx / FRAMES_PER_TEST;
                    const dotX = 0.5 + 0.35 * Math.sin(t * Math.PI * 4);
                    const dotY = 0.5 + 0.25 * Math.cos(t * Math.PI * 3);

                    // Draw dot on webcam overlay
                    if (overlayCtx && overlayCanvas) {
                        overlayCanvas.width = webcamVideo.videoWidth || 640;
                        overlayCanvas.height = webcamVideo.videoHeight || 480;
                        overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
                        // Outer glow
                        overlayCtx.beginPath();
                        overlayCtx.arc(dotX * overlayCanvas.width, dotY * overlayCanvas.height, 20, 0, Math.PI * 2);
                        overlayCtx.fillStyle = 'rgba(231, 76, 60, 0.3)';
                        overlayCtx.fill();
                        // Inner dot
                        overlayCtx.beginPath();
                        overlayCtx.arc(dotX * overlayCanvas.width, dotY * overlayCanvas.height, 10, 0, Math.PI * 2);
                        overlayCtx.fillStyle = '#e74c3c';
                        overlayCtx.fill();
                        overlayCtx.strokeStyle = '#ffffff';
                        overlayCtx.lineWidth = 3;
                        overlayCtx.stroke();
                    }
                    return { stimulus_position: { x: dotX, y: dotY } };
                },
                // onFrame
                (result) => {
                    if (result.gaze_x != null && result.gaze_y != null && overlayCtx && overlayCanvas) {
                        overlayCtx.beginPath();
                        overlayCtx.arc(result.gaze_x * overlayCanvas.width, result.gaze_y * overlayCanvas.height, 5, 0, Math.PI * 2);
                        overlayCtx.fillStyle = 'rgba(46, 204, 113, 0.7)';
                        overlayCtx.fill();
                    }
                },
                null // no onStart needed
            );
        });
    }

    // ===========================================================================
    // TEST 2: FACIAL EXPRESSION REACTION
    // ===========================================================================
    if (startExpressionTest) {
        startExpressionTest.addEventListener('click', () => {
            testInstructions.textContent = 'Mimic the expression shown below. Each emotion displayed for a few seconds.';
            currentEmotionIndex = 0;

            startTestCapture('facial_expression',
                // getExtraData: cycle through emotions
                (frameIdx) => {
                    const emotionIdx = Math.min(
                        Math.floor(frameIdx / Math.ceil(FRAMES_PER_TEST / EMOTIONS.length)),
                        EMOTIONS.length - 1
                    );
                    const emotion = EMOTIONS[emotionIdx];

                    // Update the large emotion card
                    const emojiEl = document.getElementById('emotionEmoji');
                    const labelEl = document.getElementById('emotionLabel');
                    const instructionEl = document.getElementById('emotionInstruction');
                    if (emojiEl) emojiEl.textContent = emotion.emoji;
                    if (labelEl) labelEl.textContent = emotion.name;
                    if (instructionEl) instructionEl.textContent = emotion.instruction;

                    // Flash the card border when emotion changes
                    if (emotionIdx !== currentEmotionIndex) {
                        currentEmotionIndex = emotionIdx;
                        const card = document.getElementById('emotionCard');
                        if (card) {
                            card.style.borderColor = '#ff3838';
                            setTimeout(() => { card.style.borderColor = ''; }, 300);
                        }
                        playBeep(800, 100); // beep on emotion change
                    }

                    return { target_emotion: emotion.name };
                },
                // onFrame
                (result) => {
                    if (result.detected_emotion) {
                        const matchIcon = result.expression_match ? '✅' : '❌';
                        setTestStatus('expression',
                            `${matchIcon} Detected: ${result.detected_emotion} (${(result.emotion_confidence * 100).toFixed(0)}%)`
                        );
                    }
                },
                // onStart: show the emotion stimulus AFTER stopActiveTest
                () => {
                    const emotionStimulus = document.getElementById('emotionStimulus');
                    if (emotionStimulus) emotionStimulus.classList.remove('hidden');
                    // Set initial emotion
                    const emojiEl = document.getElementById('emotionEmoji');
                    const labelEl = document.getElementById('emotionLabel');
                    const instructionEl = document.getElementById('emotionInstruction');
                    if (emojiEl) emojiEl.textContent = EMOTIONS[0].emoji;
                    if (labelEl) labelEl.textContent = EMOTIONS[0].name;
                    if (instructionEl) instructionEl.textContent = EMOTIONS[0].instruction;
                }
            );
        });
    }

    // ===========================================================================
    // TEST 3: HEAD MOVEMENT ANALYSIS
    // ===========================================================================
    if (startHeadTest) {
        startHeadTest.addEventListener('click', () => {
            testInstructions.textContent = 'Sit naturally. We will observe your head posture and movements. Try to stay relaxed.';

            startTestCapture('head_movement',
                null, // no extra data needed
                // onFrame: draw head pose feedback on overlay
                (result) => {
                    if (overlayCtx && overlayCanvas) {
                        overlayCanvas.width = webcamVideo.videoWidth || 640;
                        overlayCanvas.height = webcamVideo.videoHeight || 480;
                        overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);

                        const cx = overlayCanvas.width / 2;
                        const cy = overlayCanvas.height / 2;

                        if (result.face_detected && result.head_pitch != null) {
                            // Draw a head orientation indicator
                            const pitch = result.head_pitch || 0;
                            const yaw = result.head_yaw || 0;
                            const roll = result.head_roll || 0;

                            // Background panel
                            overlayCtx.fillStyle = 'rgba(0, 0, 0, 0.6)';
                            overlayCtx.roundRect(10, 10, 220, 100, 8);
                            overlayCtx.fill();

                            // Text readouts
                            overlayCtx.fillStyle = '#00ff88';
                            overlayCtx.font = 'bold 14px monospace';
                            overlayCtx.fillText(`↕ Pitch: ${pitch.toFixed(1)}°`, 20, 35);
                            overlayCtx.fillText(`↔ Yaw:   ${yaw.toFixed(1)}°`, 20, 58);
                            overlayCtx.fillText(`↻ Roll:  ${roll.toFixed(1)}°`, 20, 81);

                            // Draw a crosshair showing head direction
                            const indicatorX = cx + yaw * 3;
                            const indicatorY = cy + pitch * 3;

                            // Crosshair lines
                            overlayCtx.strokeStyle = 'rgba(0, 206, 201, 0.5)';
                            overlayCtx.lineWidth = 1;
                            overlayCtx.beginPath();
                            overlayCtx.moveTo(indicatorX - 30, indicatorY);
                            overlayCtx.lineTo(indicatorX + 30, indicatorY);
                            overlayCtx.moveTo(indicatorX, indicatorY - 30);
                            overlayCtx.lineTo(indicatorX, indicatorY + 30);
                            overlayCtx.stroke();

                            // Center dot
                            overlayCtx.beginPath();
                            overlayCtx.arc(indicatorX, indicatorY, 8, 0, Math.PI * 2);
                            overlayCtx.fillStyle = 'rgba(0, 206, 201, 0.8)';
                            overlayCtx.fill();
                            overlayCtx.strokeStyle = '#fff';
                            overlayCtx.lineWidth = 2;
                            overlayCtx.stroke();
                        } else {
                            // No face message
                            overlayCtx.fillStyle = 'rgba(0, 0, 0, 0.6)';
                            overlayCtx.roundRect(cx - 100, cy - 20, 200, 40, 8);
                            overlayCtx.fill();
                            overlayCtx.fillStyle = '#ff6b6b';
                            overlayCtx.font = 'bold 16px sans-serif';
                            overlayCtx.textAlign = 'center';
                            overlayCtx.fillText('No face detected', cx, cy + 6);
                            overlayCtx.textAlign = 'start';
                        }
                    }

                    if (result.head_pitch != null) {
                        setTestStatus('head', `Pitch: ${result.head_pitch}° | Yaw: ${result.head_yaw}° | Roll: ${result.head_roll}°`);
                    }
                },
                null
            );
        });
    }

    // ===========================================================================
    // TEST 4: REACTION TO STIMULI
    // ===========================================================================
    if (startReactionTest) {
        startReactionTest.addEventListener('click', () => {
            testInstructions.textContent = 'Look at each shape/flash as soon as it appears! Listen for the sound cue.';

            startTestCapture('reaction_stimulus',
                // getExtraData: show random stimuli every few frames
                (frameIdx) => {
                    const stimulusShape = document.getElementById('stimulusShape');

                    if (frameIdx % 4 === 0 && stimulusShape) {
                        const shapeIdx = Math.floor(Math.random() * SHAPES.length);
                        const color = SHAPE_COLORS[shapeIdx];
                        const shape = SHAPES[shapeIdx];

                        // Reset styles
                        stimulusShape.style.border = 'none';
                        stimulusShape.style.borderLeft = 'none';
                        stimulusShape.style.borderRight = 'none';
                        stimulusShape.style.borderBottom = 'none';
                        stimulusShape.style.width = '70px';
                        stimulusShape.style.height = '70px';
                        stimulusShape.style.background = color;
                        stimulusShape.style.display = 'block';
                        stimulusShape.style.transform = 'none';
                        stimulusShape.style.clipPath = 'none';
                        stimulusShape.style.boxShadow = `0 0 25px ${color}, 0 0 50px ${color}80`;

                        if (shape === 'circle') {
                            stimulusShape.style.borderRadius = '50%';
                        } else if (shape === 'square') {
                            stimulusShape.style.borderRadius = '8px';
                        } else if (shape === 'triangle') {
                            stimulusShape.style.background = 'transparent';
                            stimulusShape.style.width = '0';
                            stimulusShape.style.height = '0';
                            stimulusShape.style.borderLeft = '35px solid transparent';
                            stimulusShape.style.borderRight = '35px solid transparent';
                            stimulusShape.style.borderBottom = `70px solid ${color}`;
                            stimulusShape.style.borderRadius = '0';
                            stimulusShape.style.boxShadow = 'none';
                        } else if (shape === 'star') {
                            stimulusShape.style.borderRadius = '0';
                            stimulusShape.style.clipPath = 'polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%)';
                        }

                        // Animate entrance
                        stimulusShape.style.transition = 'none';
                        stimulusShape.style.opacity = '0';
                        stimulusShape.offsetHeight; // force reflow
                        stimulusShape.style.transition = 'opacity 0.1s ease, transform 0.2s ease';
                        stimulusShape.style.opacity = '1';
                        stimulusShape.style.transform = 'scale(1.15)';
                        setTimeout(() => { stimulusShape.style.transform = 'scale(1)'; }, 200);

                        // Play a beep sound
                        playBeep(400 + shapeIdx * 200, 120);

                        // Flash the webcam overlay too
                        if (overlayCtx && overlayCanvas) {
                            overlayCanvas.width = webcamVideo.videoWidth || 640;
                            overlayCanvas.height = webcamVideo.videoHeight || 480;
                            overlayCtx.fillStyle = color + '30';
                            overlayCtx.fillRect(0, 0, overlayCanvas.width, overlayCanvas.height);
                            setTimeout(() => {
                                overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
                            }, 200);
                        }

                        const rect = stimulusShape.getBoundingClientRect();
                        const sx = (rect.left + rect.width / 2) / window.innerWidth;
                        const sy = (rect.top + rect.height / 2) / window.innerHeight;
                        return { stimulus_position: { x: sx, y: sy } };
                    } else if (frameIdx % 4 === 2 && stimulusShape) {
                        // Hide shape between appearances
                        stimulusShape.style.opacity = '0.2';
                    }
                    return {};
                },
                // onFrame
                (result) => {
                    if (result.engagement_level != null) {
                        const pct = (result.engagement_level * 100).toFixed(0);
                        const bar = '█'.repeat(Math.round(result.engagement_level * 10)) + '░'.repeat(10 - Math.round(result.engagement_level * 10));
                        setTestStatus('reaction', `Engagement: ${bar} ${pct}%`);
                    }
                },
                // onStart: show the stimulus display area
                () => {
                    const stimulusDisplay = document.getElementById('stimulusDisplay');
                    const stimulusShape = document.getElementById('stimulusShape');
                    if (stimulusDisplay) stimulusDisplay.classList.remove('hidden');
                    if (stimulusShape) {
                        stimulusShape.style.display = 'block';
                        stimulusShape.style.width = '70px';
                        stimulusShape.style.height = '70px';
                        stimulusShape.style.background = '#888';
                        stimulusShape.style.borderRadius = '50%';
                        stimulusShape.style.opacity = '0.3';
                    }
                }
            );
        });
    }

    // ===========================================================================
    // ANALYZE SESSION
    // ===========================================================================
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', async () => {
            if (!sessionId) { showError('No active session.'); return; }
            clearError();
            analyzeBtn.disabled = true;
            analyzeLoading.classList.remove('hidden');

            try {
                const analyzeRes = await fetch('/autism-screening/api/analyze-session', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionId })
                });
                if (!analyzeRes.ok) {
                    throw new Error((await analyzeRes.json()).detail || 'Analysis failed');
                }

                const reportRes = await fetch(`/autism-screening/api/report/${sessionId}`);
                if (!reportRes.ok) {
                    throw new Error((await reportRes.json()).detail || 'Report generation failed');
                }
                const report = await reportRes.json();
                analyzeLoading.classList.add('hidden');
                renderResults(report);
            } catch (err) {
                analyzeLoading.classList.add('hidden');
                analyzeBtn.disabled = false;
                showError('Analysis failed: ' + err.message);
            }
        });
    }

    // ===========================================================================
    // RENDER RESULTS DASHBOARD
    // ===========================================================================
    function renderResults(report) {
        resultsDashboard.classList.remove('hidden');
        analyzeSection.classList.add('hidden');

        const analysis = report.analysis;
        const features = analysis.features;
        resultsDashboard.scrollIntoView({ behavior: 'smooth' });

        // --- Score circle ---
        const scoreValue = document.getElementById('scoreValue');
        const scoreCircle = document.getElementById('scoreCircle');
        const screeningLevel = document.getElementById('screeningLevel');
        const confidenceValue = document.getElementById('confidenceValue');

        if (scoreValue) scoreValue.textContent = analysis.screening_score.toFixed(0);
        if (screeningLevel) screeningLevel.textContent = analysis.screening_level;
        if (confidenceValue) confidenceValue.textContent = (analysis.confidence * 100).toFixed(1) + '%';

        if (scoreCircle) {
            const pct = analysis.screening_score;
            let color = '#00b894';
            if (pct > 60) color = '#e17055';
            else if (pct > 30) color = '#fdcb6e';
            scoreCircle.style.background = `conic-gradient(${color} ${pct}%, var(--border-primary) ${pct}%)`;
        }

        // --- Feature values ---
        const setFeature = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        setFeature('featureBlinkRate', features.blink_rate.toFixed(1));
        setFeature('featureGazeFixation', features.gaze_fixation_time.toFixed(3));
        setFeature('featureEmotionVar', features.emotion_variability.toFixed(3));
        setFeature('featureHeadMotion', features.head_motion_variance.toFixed(2));
        setFeature('featureReactionTime', features.reaction_time.toFixed(0));
        setFeature('featureEngagement', features.engagement_score.toFixed(3));

        // --- Charts ---
        const isDark = htmlElement.hasAttribute('data-theme');
        const chartTextColor = isDark ? '#e0e0e0' : '#333';
        const chartGridColor = isDark ? '#2d2d44' : '#e0e0e0';
        Chart.defaults.color = chartTextColor;
        Chart.defaults.borderColor = chartGridColor;

        Object.values(chartInstances).forEach(c => c.destroy());
        chartInstances = {};

        // Emotion Distribution (doughnut)
        const emotionData = report.emotion_distribution || [];
        if (emotionData.length > 0) {
            const ctx = document.getElementById('emotionChart');
            if (ctx) {
                chartInstances.emotion = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: emotionData.map(d => d.label),
                        datasets: [{
                            data: emotionData.map(d => d.value),
                            backgroundColor: ['#6c5ce7', '#00cec9', '#fdcb6e', '#e17055', '#a29bfe'],
                            borderWidth: 2,
                            borderColor: isDark ? '#1a1a2e' : '#fff'
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { position: 'bottom', labels: { padding: 15, usePointStyle: true } } }
                    }
                });
            }
        }

        // Reaction Times (bar)
        const reactionData = report.reaction_times || [];
        if (reactionData.length > 0) {
            const ctx = document.getElementById('reactionChart');
            if (ctx) {
                chartInstances.reaction = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: reactionData.map(d => d.label),
                        datasets: [{
                            label: 'Reaction Time (ms)',
                            data: reactionData.map(d => d.value),
                            backgroundColor: 'rgba(108, 92, 231, 0.7)',
                            borderColor: '#6c5ce7',
                            borderWidth: 1,
                            borderRadius: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: { y: { beginAtZero: true, title: { display: true, text: 'ms' } } },
                        plugins: { legend: { display: false } }
                    }
                });
            }
        }

        // Head Movement (line)
        const headData = report.head_movement_data || [];
        if (headData.length > 0) {
            const ctx = document.getElementById('headMovementChart');
            if (ctx) {
                chartInstances.head = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: headData.map(d => d.label),
                        datasets: [{
                            label: 'Total Angular Movement',
                            data: headData.map(d => d.value),
                            borderColor: '#00cec9',
                            backgroundColor: 'rgba(0, 206, 201, 0.1)',
                            fill: true,
                            tension: 0.4,
                            pointRadius: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: { y: { beginAtZero: true, title: { display: true, text: 'Degrees' } } },
                        plugins: { legend: { display: false } }
                    }
                });
            }
        }

        // Gaze Heatmap (canvas scatter)
        const gazeData = report.gaze_heatmap_data || [];
        if (gazeData.length > 0) {
            const heatCanvas = document.getElementById('gazeHeatmapCanvas');
            if (heatCanvas) {
                const hctx = heatCanvas.getContext('2d');
                const cw = heatCanvas.width;
                const ch = heatCanvas.height;
                hctx.fillStyle = isDark ? '#1a1a2e' : '#f8f9fa';
                hctx.fillRect(0, 0, cw, ch);
                hctx.strokeStyle = chartGridColor;
                hctx.lineWidth = 0.5;
                for (let i = 0; i <= 10; i++) {
                    hctx.beginPath(); hctx.moveTo(i * cw / 10, 0); hctx.lineTo(i * cw / 10, ch); hctx.stroke();
                    hctx.beginPath(); hctx.moveTo(0, i * ch / 10); hctx.lineTo(cw, i * ch / 10); hctx.stroke();
                }
                gazeData.forEach(point => {
                    const px = point.x * cw;
                    const py = point.y * ch;
                    const intensity = point.intensity || 0.5;
                    const radius = 4 + intensity * 6;
                    const alpha = 0.2 + intensity * 0.5;
                    hctx.beginPath();
                    hctx.arc(px, py, radius, 0, Math.PI * 2);
                    hctx.fillStyle = `rgba(108, 92, 231, ${alpha})`;
                    hctx.fill();
                });
                hctx.fillStyle = chartTextColor;
                hctx.font = '10px sans-serif';
                hctx.fillText('Gaze Points Distribution', 8, 15);
            }
        }
    }
});
