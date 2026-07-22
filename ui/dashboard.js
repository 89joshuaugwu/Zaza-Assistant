function closeDashboard() {
    if (window.pywebview) {
        window.pywebview.api.close_dashboard();
    }
}

function toggleWakeSettings() {
    const mode = document.getElementById('wake-mode').value;
    if (mode === 'model') {
        document.getElementById('wake-model-group').style.display = 'flex';
        document.getElementById('wake-word-group').style.display = 'none';
    } else {
        document.getElementById('wake-model-group').style.display = 'none';
        document.getElementById('wake-word-group').style.display = 'flex';
    }
}

function saveSettings() {
    const wakeMode = document.getElementById('wake-mode').value;
    const wakeModel = document.getElementById('wake-model').value;
    const wakeWord = document.getElementById('wake-word').value;
    const whisperModel = document.getElementById('whisper-model').value;
    const ollamaModel = document.getElementById('ollama-model').value;
    
    if (window.pywebview) {
        window.pywebview.api.save_settings({
            'WAKE_MODE': wakeMode,
            'WAKE_MODEL': wakeModel,
            'WAKE_WORD': wakeWord,
            'WHISPER_MODEL_SIZE': whisperModel,
            'OLLAMA_MODEL': ollamaModel
        }).then(() => {
            const status = document.getElementById('save-status');
            status.style.display = 'block';
            setTimeout(() => { status.style.display = 'none'; }, 3000);
        });
    }
}

// Load settings on init
window.addEventListener('pywebviewready', function() {
    window.pywebview.api.get_settings().then(settings => {
        if(settings.WAKE_MODE) {
            document.getElementById('wake-mode').value = settings.WAKE_MODE;
            toggleWakeSettings();
        }
        if(settings.WAKE_MODEL) document.getElementById('wake-model').value = settings.WAKE_MODEL;
        if(settings.WAKE_WORD) document.getElementById('wake-word').value = settings.WAKE_WORD;
        if(settings.WHISPER_MODEL_SIZE) document.getElementById('whisper-model').value = settings.WHISPER_MODEL_SIZE;
        if(settings.OLLAMA_MODEL) document.getElementById('ollama-model').value = settings.OLLAMA_MODEL;
    });
});
